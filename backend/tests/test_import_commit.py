import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.academic import Teacher
from app.models.user import Role, User

client = TestClient(app)
FIXTURE = Path(__file__).parent / "fixtures" / "teachers_mixed.csv"


def _admin_headers() -> dict:
    db = SessionLocal()
    u = User(email=f"a-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=Role.admin)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='admin')}"}


def _preview(h):
    fac = f"F-{uuid.uuid4().hex[:6]}"
    fid = client.post("/faculties", json={"name": fac}, headers=h).json()["id"]
    client.post("/departments", json={"name": "CS", "faculty_id": fid}, headers=h)
    did = client.get("/departments", params={"faculty_id": fid}, headers=h).json()[0]["id"]
    existing = f"EMP{uuid.uuid4().hex[:8]}"
    client.post("/teachers", json={
        "employee_id": existing, "full_name": "Already Here", "dob": "1980-01-01",
        "faculty_id": fid, "department_id": did,
    }, headers=h)
    tag = uuid.uuid4().hex[:6].upper()
    csv = (FIXTURE.read_text().replace("{FAC}", fac).replace("{DEP}", "CS")
           .replace("{EXISTING}", existing).replace("IMP", f"I{tag}").replace("@x.local", f"-{tag}@x.local"))
    body = client.post("/teachers/import/preview",
                       files={"file": ("t.csv", csv, "text/csv")}, headers=h).json()
    return body, existing


def _pw_hash(emp_id: str) -> str:
    db = SessionLocal()
    t = db.query(Teacher).filter_by(employee_id=emp_id).first()
    u = db.get(User, t.user_id)
    h = u.password_hash
    db.close()
    return h


def test_commit_skip_creates_valid_only():
    h = _admin_headers()
    preview, existing = _preview(h)
    r = client.post("/teachers/import/commit",
                    json={"import_id": preview["import_id"], "duplicate_action": "skip"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json() == {"created": 1, "updated": 0, "skipped": 1, "rejected": 4}

    db = SessionLocal()
    still = db.query(Teacher).filter_by(employee_id=existing).first()
    assert still.full_name == "Already Here"  # untouched
    db.close()

    # consumed → 410
    again = client.post("/teachers/import/commit",
                        json={"import_id": preview["import_id"], "duplicate_action": "skip"}, headers=h)
    assert again.status_code == 410


def test_commit_override_updates_profile_not_password():
    h = _admin_headers()
    preview, existing = _preview(h)
    pw_before = _pw_hash(existing)

    r = client.post("/teachers/import/commit",
                    json={"import_id": preview["import_id"], "duplicate_action": "override"}, headers=h)
    assert r.status_code == 200
    assert r.json()["updated"] == 1

    db = SessionLocal()
    t = db.query(Teacher).filter_by(employee_id=existing).first()
    assert t.full_name == "Db Dupe" and t.designation == "Professor"
    db.close()
    assert _pw_hash(existing) == pw_before  # password untouched


def test_unknown_import_id_404():
    h = _admin_headers()
    r = client.post("/teachers/import/commit",
                    json={"import_id": str(uuid.uuid4()), "duplicate_action": "skip"}, headers=h)
    assert r.status_code == 404
