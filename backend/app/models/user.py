import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import PKMixin, TimestampMixin


class Role(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    kiosk = "kiosk"


class User(Base, PKMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    force_password_reset: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
