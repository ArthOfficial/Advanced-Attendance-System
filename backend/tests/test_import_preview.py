import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)
FIXTURE = Path(__file__).parent / "fixtures" / "teachers_mixed.csv"


def _admin_headers() -> dict:
    db = SessionLocal()
    u = User(email=f"a-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=Role.admin)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='admin')}"}


def _setup(h):
    fac = f"F-{uuid.uuid4().hex[:6]}"
    fid = client.post("/faculties", json={"name": fac}, headers=h).json()["id"]
    dep = "CS"
    client.post("/departments", json={"name": dep, "faculty_id": fid}, headers=h)
    existing_emp = f"EMP{uuid.uuid4().hex[:8]}"
    did = client.get("/departments", params={"faculty_id": fid}, headers=h).json()[0]["id"]
    client.post("/teachers", json={
        "employee_id": existing_emp, "full_name": "Already Here", "dob": "1980-01-01",
        "faculty_id": fid, "department_id": did,
    }, headers=h)
    return fac, dep, existing_emp


def test_preview_classifies_rows():
    h = _admin_headers()
    fac, dep, existing = _setup(h)
    tag = uuid.uuid4().hex[:6].upper()
    csv = (FIXTURE.read_text().replace("{FAC}", fac).replace("{DEP}", dep)
           .replace("{EXISTING}", existing).replace("IMP", f"I{tag}").replace("@x.local", f"-{tag}@x.local"))

    r = client.post("/teachers/import/preview",
                    files={"file": ("teachers.csv", csv, "text/csv")}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["counts"] == {"valid": 1, "duplicates": 1, "rejected": 4}
    assert body["valid"][0]["employee_id"] == f"I{tag}001"
    dup = body["duplicates"][0]
    assert dup["row"]["employee_id"] == existing
    assert dup["existing"]["full_name"] == "Already Here"
    reasons = {x["reason"] for x in body["rejected"]}
    assert reasons == {"duplicate in file", "unknown department", "invalid dob",
                       "missing required field: employee_id"}
    assert body["import_id"]

    # preview writes no teachers
    check = client.get("/teachers", params={"q": f"I{tag}001"}, headers=h)
    assert check.json() == []
