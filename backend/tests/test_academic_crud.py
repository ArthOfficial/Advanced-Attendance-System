import uuid

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
    tok = security.create_access_token(sub=str(u.id), role="admin")
    return {"Authorization": f"Bearer {tok}"}


def _teacher_headers() -> dict:
    db = SessionLocal()
    u = User(email=f"t-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=Role.teacher)
    db.add(u); db.commit(); db.refresh(u); db.close()
    tok = security.create_access_token(sub=str(u.id), role="teacher")
    return {"Authorization": f"Bearer {tok}"}


def test_full_crud_and_guards():
    h = _admin_headers()
    name = f"Fac-{uuid.uuid4().hex[:6]}"

    r = client.post("/faculties", json={"name": name}, headers=h)
    assert r.status_code == 201
    fid = r.json()["id"]

    # duplicate name (case-insensitive) → 409
    assert client.post("/faculties", json={"name": name.upper()}, headers=h).status_code == 409

    r = client.post("/departments", json={"name": "CS", "faculty_id": fid}, headers=h)
    assert r.status_code == 201
    did = r.json()["id"]

    # faculty with department → delete blocked
    assert client.delete(f"/faculties/{fid}", headers=h).status_code == 409

    # teacher role blocked entirely
    assert client.get("/faculties", headers=_teacher_headers()).status_code == 403

    # delete department then faculty
    assert client.delete(f"/departments/{did}", headers=h).status_code == 204
    assert client.delete(f"/faculties/{fid}", headers=h).status_code == 204
