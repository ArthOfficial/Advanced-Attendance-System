import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import PKMixin, TimestampMixin


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"


class AttendanceMethod(str, enum.Enum):
    QR = "QR"
    FACE = "FACE"
    RFID = "RFID"
    NFC = "NFC"


class AttendanceSession(Base, PKMixin, TimestampMixin):
    __tablename__ = "attendance_sessions"
    session_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    session_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Attendance(Base, PKMixin, TimestampMixin):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("teacher_id", "session_id", name="uq_attendance_teacher_session"),)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("attendance_sessions.id"), nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus, name="attendance_status"), nullable=False)
    attendance_method: Mapped[AttendanceMethod] = mapped_column(
        Enum(AttendanceMethod, name="attendance_method"), default=AttendanceMethod.QR, nullable=False
    )
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class QRToken(Base, PKMixin, TimestampMixin):
    __tablename__ = "qr_tokens"
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("attendance_sessions.id"), nullable=False)
    kiosk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("attendance_kiosks.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
