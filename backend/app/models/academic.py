import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import PKMixin, TimestampMixin


class Faculty(Base, PKMixin, TimestampMixin):
    __tablename__ = "faculties"
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class Department(Base, PKMixin, TimestampMixin):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("faculty_id", "name", name="uq_department_faculty_name"),)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faculties.id"), nullable=False
    )


class Teacher(Base, PKMixin, TimestampMixin):
    __tablename__ = "teachers"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculties.id"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    designation: Mapped[str] = mapped_column(String(128), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
