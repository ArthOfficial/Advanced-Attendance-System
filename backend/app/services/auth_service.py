from app.core import security
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenPair
from app.services.base import BaseService


class AuthService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.users = UserRepository(db)

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.users.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not security.verify_password(password, user.password_hash):
            return None
        return user

    def login(self, email: str, password: str) -> TokenPair | None:
        user = self.authenticate(email, password)
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
        return True
