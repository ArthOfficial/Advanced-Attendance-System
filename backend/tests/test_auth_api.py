# ponytail: hits the real Postgres test DB (alembic upgrade head must have run).
import uuid

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)


def _mk_user(email, role, pw="pw12345"):
    db = SessionLocal()
    u = User(id=uuid.uuid4(), email=email, password_hash=security.hash_password(pw), role=role)
    db.add(u)
    db.commit()
    db.close()


def test_login_and_rbac_flow():
    email = f"admin-{uuid.uuid4().hex[:8]}@x.io"
    _mk_user(email, Role.admin)

    r = client.post("/auth/login", json={"email": email, "password": "pw12345"})
    assert r.status_code == 200
    assert r.json()["access_token"]

    bad = client.post("/auth/login", json={"email": email, "password": "nope"})
    assert bad.status_code == 401
