import uuid

from app.database import SessionLocal
from app.models.user import Role
from app.repositories.user_repo import UserRepository

# ponytail: runs against the Postgres test DB (alembic upgrade head must have run).
# postgresql.UUID/JSONB do not compile on SQLite, so no in-memory shortcut.


def test_get_by_email_roundtrip():
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        email = f"repo-{uuid.uuid4().hex[:8]}@x.io"
        repo.create(email=email, password_hash="h", role=Role.admin)
        found = repo.get_by_email(email)
        assert found is not None and found.role == Role.admin
        assert repo.get_by_email("missing@x.io") is None
    finally:
        db.close()
