# ponytail: spec-required placeholders. Defined, never written in V1. Do not build features on these.
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import PKMixin, TimestampMixin


class FaceProfile(Base, PKMixin, TimestampMixin):
    __tablename__ = "face_profiles"
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=True)


class FaceEmbedding(Base, PKMixin, TimestampMixin):
    __tablename__ = "face_embeddings"
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("face_profiles.id"), nullable=True)
    vector: Mapped[dict] = mapped_column(JSONB, nullable=True)


class FaceVerificationLog(Base, PKMixin, TimestampMixin):
    __tablename__ = "face_verification_logs"
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=True)
    result: Mapped[str] = mapped_column(String(64), nullable=True)
