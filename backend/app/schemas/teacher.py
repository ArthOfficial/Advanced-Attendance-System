import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class TeacherCreate(BaseModel):
    employee_id: str
    full_name: str
    dob: date
    faculty_id: uuid.UUID
    department_id: uuid.UUID
    designation: str | None = None
    email: str | None = None


class TeacherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    employee_id: str
    full_name: str
    dob: date
    faculty_id: uuid.UUID
    department_id: uuid.UUID
    designation: str | None
    email: str | None


class TeacherMe(TeacherOut):
    faculty_name: str
    department_name: str
    force_password_reset: bool
