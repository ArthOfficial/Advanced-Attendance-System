from app.core import security
from app.core.audit import audit
from app.models.user import User
from app.repositories.teacher_repo import TeacherRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenPair
from app.services.base import BaseService


class AuthService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.users = UserRepository(db)
        self.teachers = TeacherRepository(db)

    def _resolve(self, identifier: str) -> User | None:
        teacher = self.teachers.get_by_employee_id(identifier)
        if teacher:
            return self.users.get(teacher.user_id)
        return self.users.get_by_email(identifier)

    def authenticate(self, identifier: str, password: str) -> User | None:
        user = self._resolve(identifier)
        if not user or not user.is_active:
            audit(self.db, None, "auth.login.failure", detail={"identifier": identifier})
            return None
        if not security.verify_password(password, user.password_hash):
            audit(self.db, user.id, "auth.login.failure", detail={"identifier": identifier})
            return None
        audit(self.db, user.id, "auth.login.success")
        return user

    def login(self, identifier: str, password: str) -> TokenPair | None:
        user = self.authenticate(identifier, password)
        if user is None:
            return None
        return TokenPair(
            access_token=security.create_access_token(sub=str(user.id), role=user.role.value),
            refresh_token=security.create_refresh_token(sub=str(user.id)),
            force_password_reset=user.force_password_reset,
        )

    def change_password(self, user: User, old: str, new: str) -> bool:
        if not security.verify_password(old, user.password_hash):
            return False
        user.password_hash = security.hash_password(new)
        user.force_password_reset = False
        self.db.commit()
        audit(self.db, user.id, "auth.password_changed")
        return True
