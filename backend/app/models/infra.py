import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import PKMixin, TimestampMixin


class AttendanceKiosk(Base, PKMixin, TimestampMixin):
    __tablename__ = "attendance_kiosks"
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Device(Base, PKMixin, TimestampMixin):
    __tablename__ = "devices"
    fingerprint: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=True)


class AuditLog(Base, PKMixin, TimestampMixin):
    __tablename__ = "audit_logs"
    actor_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity: Mapped[str] = mapped_column(String(128), nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=True)
    ip: Mapped[str] = mapped_column(String(64), nullable=True)


class SystemSetting(Base, PKMixin, TimestampMixin):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=True)
