import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.academic import Department, Faculty, Teacher
from app.models.user import Role, User

client = TestClient(app)


def _mk_teacher(emp_id: str, pw: str = "15081990", email: str | None = None):
    db = SessionLocal()
    fac = Faculty(name=f"Fac-{uuid.uuid4().hex[:6]}")
    db.add(fac); db.flush()
    dep = Department(name=f"Dep-{uuid.uuid4().hex[:6]}", faculty_id=fac.id)
    db.add(dep); db.flush()
    u = User(email=email, password_hash=security.hash_password(pw), role=Role.teacher,
             force_password_reset=True)
    db.add(u); db.flush()
    t = Teacher(user_id=u.id, faculty_id=fac.id, department_id=dep.id, employee_id=emp_id,
                full_name="T Teacher", dob=date(1990, 8, 15))
    db.add(t); db.commit(); db.close()


def test_teacher_logs_in_with_employee_id_no_email():
    emp = f"EMP{uuid.uuid4().hex[:8]}"
    _mk_teacher(emp, email=None)
    r = client.post("/auth/login", json={"identifier": emp, "password": "15081990"})
    assert r.status_code == 200
    assert r.json()["force_password_reset"] is True


def test_admin_still_logs_in_with_email():
    email = f"adm-{uuid.uuid4().hex[:6]}@smartcampus.local"
    db = SessionLocal()
    db.add(User(email=email, password_hash=security.hash_password("pw12345"), role=Role.admin))
    db.commit(); db.close()
    r = client.post("/auth/login", json={"identifier": email, "password": "pw12345"})
    assert r.status_code == 200


def test_wrong_password_401():
    emp = f"EMP{uuid.uuid4().hex[:8]}"
    _mk_teacher(emp)
    assert client.post("/auth/login", json={"identifier": emp, "password": "x"}).status_code == 401
