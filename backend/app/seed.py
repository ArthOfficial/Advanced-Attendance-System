from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import Role
from app.repositories.user_repo import UserRepository


def seed_admin() -> None:
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if repo.get_by_email(settings.first_admin_email):
            return
        repo.create(
            email=settings.first_admin_email,
            password_hash=hash_password(settings.first_admin_password),
            role=Role.admin,
            force_password_reset=True,
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
