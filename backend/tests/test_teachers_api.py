import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)


def _admin_headers() -> dict:
    db = SessionLocal()
    u = User(email=f"a-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=Role.admin)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='admin')}"}


def _mk_academic(h):
    fid = client.post("/faculties", json={"name": f"F-{uuid.uuid4().hex[:6]}"}, headers=h).json()["id"]
    did = client.post("/departments", json={"name": "CS", "faculty_id": fid}, headers=h).json()["id"]
    return fid, did


def test_create_teacher_and_dob_login_and_me():
    h = _admin_headers()
    fid, did = _mk_academic(h)
    emp = f"EMP{uuid.uuid4().hex[:8]}"

    r = client.post("/teachers", json={
        "employee_id": emp, "full_name": "Alice Ada", "dob": "1990-08-15",
        "faculty_id": fid, "department_id": did, "designation": "Lecturer",
    }, headers=h)
    assert r.status_code == 201, r.text

    # duplicate employee_id → 409
    r2 = client.post("/teachers", json={
        "employee_id": emp, "full_name": "Bob", "dob": "1991-01-01",
        "faculty_id": fid, "department_id": did,
    }, headers=h)
    assert r2.status_code == 409

    # login with employee id + DOB password
    login = client.post("/auth/login", json={"identifier": emp, "password": "15081990"})
    assert login.status_code == 200
    assert login.json()["force_password_reset"] is True

    # /me returns profile with names
    me = client.get("/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200
    body = me.json()
    assert body["employee_id"] == emp and body["department_name"] == "CS"


def test_department_faculty_mismatch_422():
    h = _admin_headers()
    fid1, did1 = _mk_academic(h)
    fid2, _ = _mk_academic(h)
    r = client.post("/teachers", json={
        "employee_id": f"EMP{uuid.uuid4().hex[:8]}", "full_name": "X", "dob": "1990-01-01",
        "faculty_id": fid2, "department_id": did1,
    }, headers=h)
    assert r.status_code == 422
