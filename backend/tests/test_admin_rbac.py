import uuid

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)


def _token(role: Role) -> str:
    db = SessionLocal()
    u = User(id=uuid.uuid4(), email=f"{role.value}-{uuid.uuid4().hex[:6]}@x.io",
             password_hash=security.hash_password("pw"), role=role)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return security.create_access_token(sub=str(u.id), role=role.value)


def test_admin_ping_allows_admin_blocks_teacher():
    admin = _token(Role.admin)
    teacher = _token(Role.teacher)
    assert client.get("/admin/ping", headers={"Authorization": f"Bearer {admin}"}).status_code == 200
    assert client.get("/admin/ping", headers={"Authorization": f"Bearer {teacher}"}).status_code == 403
    assert client.get("/admin/ping").status_code == 401
