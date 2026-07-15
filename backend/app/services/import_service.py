import io
import uuid
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from app.models.imports import ImportBatch
from app.repositories.academic_repo import DepartmentRepository, FacultyRepository
from app.repositories.teacher_repo import TeacherRepository
from app.services.base import BaseService

REQUIRED = ["employee_id", "full_name", "dob", "faculty", "department"]
COLUMN_MAP = {
    "employee id": "employee_id", "full name": "full_name", "dob": "dob",
    "faculty": "faculty", "department": "department",
    "designation": "designation", "email": "email",
}
DOB_FORMATS = ["%d/%m/%Y", "%d-%m-%Y"]


def _parse_dob(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in DOB_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


class ImportService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.teachers = TeacherRepository(db)
        self.faculties = FacultyRepository(db)
        self.departments = DepartmentRepository(db)

    def _read(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        else:  # .xlsx / .xls via openpyxl
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        df.columns = [COLUMN_MAP.get(str(c).strip().lower(), str(c).strip().lower()) for c in df.columns]
        return df

    def preview(self, file_bytes: bytes, filename: str, actor_id: uuid.UUID) -> dict:
        df = self._read(file_bytes, filename)
        valid, duplicates, rejected = [], [], []
        seen_in_file: set[str] = set()

        for _, raw in df.iterrows():
            row = {k: (str(raw[k]).strip() if k in raw and pd.notna(raw[k]) else "")
                   for k in ["employee_id", "full_name", "dob", "faculty", "department",
                             "designation", "email"]}

            missing = next((f for f in REQUIRED if not row[f]), None)
            if missing:
                rejected.append({"row": row, "reason": f"missing required field: {missing}"})
                continue

            if row["employee_id"] in seen_in_file:
                rejected.append({"row": row, "reason": "duplicate in file"})
                continue
            seen_in_file.add(row["employee_id"])

            dob = _parse_dob(row["dob"])
            if dob is None:
                rejected.append({"row": row, "reason": "invalid dob"})
                continue
            row["dob"] = dob.isoformat()

            fac = self.faculties.get_by_name_ci(row["faculty"])
            if not fac:
                rejected.append({"row": row, "reason": "unknown faculty"})
                continue
            dep = self.departments.get_by_name_ci(fac.id, row["department"])
            if not dep:
                rejected.append({"row": row, "reason": "unknown department"})
                continue
            row["faculty_id"] = str(fac.id)
            row["department_id"] = str(dep.id)

            existing = self.teachers.get_by_employee_id(row["employee_id"])
            if existing:
                ex_fac = self.faculties.get(existing.faculty_id)
                ex_dep = self.departments.get(existing.department_id)
                duplicates.append({"row": row, "existing": {
                    "id": str(existing.id), "employee_id": existing.employee_id,
                    "full_name": existing.full_name, "dob": existing.dob.isoformat(),
                    "faculty": ex_fac.name, "department": ex_dep.name,
                    "designation": existing.designation, "email": existing.email,
                }})
                continue

            valid.append(row)

        batch = ImportBatch(
            payload={"valid": valid, "duplicates": duplicates,
                     "rejected_count": len(rejected)},
            created_by=actor_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        return {
            "import_id": str(batch.id), "valid": valid, "duplicates": duplicates,
            "rejected": rejected,
            "counts": {"valid": len(valid), "duplicates": len(duplicates), "rejected": len(rejected)},
        }
