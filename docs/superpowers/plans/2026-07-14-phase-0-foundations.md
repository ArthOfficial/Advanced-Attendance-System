# Phase 0 — Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a Dockerized FastAPI + Postgres backend with the full foundational DB schema, JWT auth, RBAC, repository/service layers, and an `AttendanceProvider` abstraction, plus a Next.js PWA scaffold — so all later phases build on it without redesign.

**Architecture:** Sync SQLAlchemy ORM over Postgres, Alembic migrations, Pydantic Settings for config. Auth via short-lived access + longer refresh JWTs (argon2 hashing). RBAC through a FastAPI dependency reading the role claim. Business logic in thin Services over generic Repositories. Attendance methods pluggable via an abstract provider + registry dict (only QR arrives later).

**Tech Stack:** FastAPI, SQLAlchemy 2.x (sync), Alembic, Pydantic v2 + pydantic-settings, PyJWT, argon2-cffi, psycopg2-binary, pytest, Docker Compose, Next.js/TypeScript/Tailwind.

## Global Constraints

- Python 3.12. UUID primary keys on every table (`uuid4` default).
- `created_at` + `updated_at` (UTC) on every table.
- Roles are exactly: `admin`, `teacher`, `kiosk`. Attendance statuses exactly: `present`, `absent`. Attendance methods: `QR`, `FACE`, `RFID`, `NFC` (only `QR` used in V1).
- All config via env vars (12-factor). No secrets in code.
- CORS restricted to LAN origins from settings.
- Placeholder tables `face_profiles`, `face_embeddings`, `face_verification_logs` are created but never written.
- Mark deliberate corner-cuts with `# ponytail:` comments. Non-trivial logic ships one runnable check.
- Update `working.md`, `phases.md` (STATUS), and `DECISIONS.md` as work progresses.

---

### Task 1: Backend scaffold running under Docker Compose

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `backend/tests/__init__.py`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `app.config.settings` (Settings instance) with `.database_url: str`, `.jwt_secret: str`, `.access_ttl_min: int`, `.refresh_ttl_days: int`, `.cors_origins: list[str]`, `.first_admin_email: str`, `.first_admin_password: str`. `app.main.app` (FastAPI). `GET /health` → `{"status": "ok"}`.

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
pydantic==2.10.3
pydantic-settings==2.6.1
pyjwt==2.10.1
argon2-cffi==23.1.0
python-multipart==0.0.19
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: Write `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://smartcampus:smartcampus@db:5432/smartcampus"
    jwt_secret: str = "change-me-in-prod"
    jwt_alg: str = "HS256"
    access_ttl_min: int = 15
    refresh_ttl_days: int = 7
    cors_origins: list[str] = ["http://localhost:3000"]
    first_admin_email: str = "admin@smartcampus.local"
    first_admin_password: str = "ChangeMe123!"


settings = Settings()
```

- [ ] **Step 3: Write `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="SmartCampus Attendance", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Write empty `backend/app/__init__.py` and `backend/tests/__init__.py`**

Both empty files.

- [ ] **Step 5: Write failing test `backend/tests/test_health.py`**

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && pip install -r requirements.txt && pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 7: Write `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 8: Write `.env.example`**

```
DATABASE_URL=postgresql+psycopg2://smartcampus:smartcampus@db:5432/smartcampus
JWT_SECRET=change-me-in-prod
ACCESS_TTL_MIN=15
REFRESH_TTL_DAYS=7
CORS_ORIGINS=["http://localhost:3000"]
FIRST_ADMIN_EMAIL=admin@smartcampus.local
FIRST_ADMIN_PASSWORD=ChangeMe123!
POSTGRES_USER=smartcampus
POSTGRES_PASSWORD=smartcampus
POSTGRES_DB=smartcampus
```

- [ ] **Step 9: Write `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-smartcampus}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-smartcampus}
      POSTGRES_DB: ${POSTGRES_DB:-smartcampus}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-smartcampus}"]
      interval: 5s
      timeout: 3s
      retries: 10
  backend:
    build: ./backend
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    command: sh -c "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    ports:
      - "8000:8000"
volumes:
  pgdata:
```

Note: `frontend` service added in Task 8. `alembic`/`seed` wired in Tasks 2 & 6 — until then run backend with plain uvicorn if testing early.

- [ ] **Step 10: Commit**

```bash
git add backend docker-compose.yml .env.example
git commit -m "feat(p0): backend scaffold + health endpoint + docker compose"
```

---

### Task 2: Database layer + full foundational schema (Alembic migration)

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/academic.py`
- Create: `backend/app/models/attendance.py`
- Create: `backend/app/models/infra.py`
- Create: `backend/app/models/face.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Test: `backend/tests/test_schema.py`

**Interfaces:**
- Produces: `app.database.Base`, `app.database.engine`, `app.database.SessionLocal`, `app.database.get_db()` (FastAPI dependency yielding a `Session`). Enums `Role`, `AttendanceStatus`, `AttendanceMethod` (str, Enum). ORM models: `User, Faculty, Department, Teacher, AttendanceKiosk, Device, AttendanceSession, Attendance, QRToken, AuditLog, SystemSetting, FaceProfile, FaceEmbedding, FaceVerificationLog`.

- [ ] **Step 1: Write `backend/app/database.py`**

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Write `backend/app/models/base.py`**

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=utcnow
    )
```

- [ ] **Step 3: Write `backend/app/models/user.py`**

```python
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
```

- [ ] **Step 4: Write `backend/app/models/academic.py`**

```python
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
```

- [ ] **Step 5: Write `backend/app/models/attendance.py`**

```python
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
```

- [ ] **Step 6: Write `backend/app/models/infra.py`**

```python
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
```

- [ ] **Step 7: Write `backend/app/models/face.py` (empty placeholder tables)**

```python
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
```

- [ ] **Step 8: Write `backend/app/models/__init__.py` (import all so metadata is complete)**

```python
from app.models.academic import Department, Faculty, Teacher
from app.models.attendance import (
    Attendance,
    AttendanceMethod,
    AttendanceSession,
    AttendanceStatus,
    QRToken,
)
from app.models.face import FaceEmbedding, FaceProfile, FaceVerificationLog
from app.models.infra import AttendanceKiosk, AuditLog, Device, SystemSetting
from app.models.user import Role, User

__all__ = [
    "Attendance", "AttendanceMethod", "AttendanceSession", "AttendanceStatus", "QRToken",
    "Department", "Faculty", "Teacher", "FaceEmbedding", "FaceProfile", "FaceVerificationLog",
    "AttendanceKiosk", "AuditLog", "Device", "SystemSetting", "Role", "User",
]
```

- [ ] **Step 9: Initialize Alembic**

Run: `cd backend && alembic init alembic`
Then edit `backend/alembic.ini`: set `sqlalchemy.url =` (leave blank; env.py supplies it).

- [ ] **Step 10: Edit `backend/alembic/env.py` to use our metadata + settings URL**

Replace the config/target_metadata section with:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base
import app.models  # noqa: F401  -- registers all tables on Base.metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 11: Autogenerate the initial migration**

Run (Postgres must be up — `docker compose up -d db`):
`cd backend && alembic revision --autogenerate -m "phase0 foundational schema"`
Expected: a file under `backend/alembic/versions/` creating all 12 core tables + 3 face tables. Eyeball it: confirm every table from Task 2 interfaces is present.

- [ ] **Step 12: Apply and verify with `backend/tests/test_schema.py`**

```python
import sqlalchemy as sa

from app.database import engine

EXPECTED = {
    "users", "faculties", "departments", "teachers", "attendance_kiosks", "devices",
    "attendance_sessions", "attendance", "qr_tokens", "audit_logs", "system_settings",
    "face_profiles", "face_embeddings", "face_verification_logs",
}


def test_all_tables_exist():
    # Requires: alembic upgrade head already run against the test DB.
    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED <= tables, f"missing: {EXPECTED - tables}"
```

Run: `cd backend && alembic upgrade head && pytest tests/test_schema.py -v`
Expected: PASS.

- [ ] **Step 13: Commit**

```bash
git add backend/app/database.py backend/app/models backend/alembic backend/alembic.ini backend/tests/test_schema.py
git commit -m "feat(p0): SQLAlchemy models + alembic foundational schema"
```

---

### Task 3: Security core — password hashing + JWT

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/security.py`
- Test: `backend/tests/test_security.py`

**Interfaces:**
- Produces: `hash_password(raw: str) -> str`; `verify_password(raw: str, hashed: str) -> bool`; `create_access_token(sub: str, role: str) -> str`; `create_refresh_token(sub: str) -> str`; `decode_token(token: str) -> dict` (raises `jwt.PyJWTError` on invalid/expired). Token payload: `{"sub", "role"?, "type": "access"|"refresh", "exp", "iat"}`.

- [ ] **Step 1: Write failing test `backend/tests/test_security.py`**

```python
import jwt
import pytest

from app.core import security


def test_password_roundtrip():
    h = security.hash_password("secret123")
    assert h != "secret123"
    assert security.verify_password("secret123", h) is True
    assert security.verify_password("wrong", h) is False


def test_access_token_carries_role():
    tok = security.create_access_token(sub="user-1", role="admin")
    payload = security.decode_token(tok)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_decode_rejects_garbage():
    with pytest.raises(jwt.PyJWTError):
        security.decode_token("not-a-token")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_security.py -v`
Expected: FAIL (module `app.core.security` not found).

- [ ] **Step 3: Write `backend/app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_ph = PasswordHasher()


def hash_password(raw: str) -> str:
    return _ph.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, raw)
    except VerifyMismatchError:
        return False


def _encode(payload: dict, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {**payload, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_access_token(sub: str, role: str) -> str:
    return _encode({"sub": sub, "role": role, "type": "access"},
                   timedelta(minutes=settings.access_ttl_min))


def create_refresh_token(sub: str) -> str:
    return _encode({"sub": sub, "type": "refresh"},
                   timedelta(days=settings.refresh_ttl_days))


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_security.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/app/core/__init__.py backend/tests/test_security.py
git commit -m "feat(p0): password hashing + JWT security core"
```

---

### Task 4: Repository + Service base classes + user repository

**Files:**
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/base.py`
- Create: `backend/app/repositories/user_repo.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/base.py`
- Test: `backend/tests/test_user_repo.py`

**Interfaces:**
- Produces: `BaseRepository(model, db)` with `.get(id)`, `.list()`, `.create(**kw)`, `.get_by(**kw)`. `UserRepository(db)` extends it, adds `.get_by_email(email) -> User | None`. `BaseService(db)` holding a `db: Session`.

- [ ] **Step 1: Write `backend/app/repositories/base.py`**

```python
import uuid
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.database import Base

M = TypeVar("M", bound=Base)


class BaseRepository(Generic[M]):
    def __init__(self, model: type[M], db: Session):
        self.model = model
        self.db = db

    def get(self, id_: uuid.UUID) -> M | None:
        return self.db.get(self.model, id_)

    def get_by(self, **kw) -> M | None:
        return self.db.query(self.model).filter_by(**kw).first()

    def list(self) -> list[M]:
        return self.db.query(self.model).all()

    def create(self, **kw) -> M:
        obj = self.model(**kw)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
```

- [ ] **Step 2: Write `backend/app/repositories/user_repo.py`**

```python
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.get_by(email=email)
```

- [ ] **Step 3: Write `backend/app/services/base.py`**

```python
from sqlalchemy.orm import Session


class BaseService:
    def __init__(self, db: Session):
        self.db = db
```

- [ ] **Step 4: Write empty `__init__.py` for both packages, then failing test `backend/tests/test_user_repo.py`**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import Role, User
from app.repositories.user_repo import UserRepository

# ponytail: SQLite in-memory for a pure-repo unit test. UUID/JSONB-heavy models
# use Postgres in integration tests; this only exercises the User table shape.


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[User.__table__])
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


def test_get_by_email_roundtrip(db):
    repo = UserRepository(db)
    repo.create(email="a@x.io", password_hash="h", role=Role.admin)
    found = repo.get_by_email("a@x.io")
    assert found is not None and found.role == Role.admin
    assert repo.get_by_email("missing@x.io") is None
```

Note: add `pysqlite3` is stdlib `sqlite3`; no extra dep. If `UUID(as_uuid=True)` fails on SQLite, add to test fixture `from sqlalchemy.dialects.postgresql import UUID` compile note — but User PK renders fine via SQLAlchemy's generic fallback. If it errors, switch this test to the Postgres integration DB used in Task 6 and mark `@pytest.mark.integration`.

- [ ] **Step 5: Run to verify pass**

Run: `cd backend && pytest tests/test_user_repo.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories backend/app/services backend/tests/test_user_repo.py
git commit -m "feat(p0): repository + service base classes + user repo"
```

---

### Task 5: Auth service + RBAC deps + auth router

**Files:**
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/auth.py`
- Modify: `backend/app/main.py` (mount auth router)
- Test: `backend/tests/test_auth_api.py`

**Interfaces:**
- Consumes: `UserRepository`, `security.*`, `get_db`.
- Produces: `AuthService(db)` with `.authenticate(email, password) -> User | None`, `.login(email, password) -> TokenPair`, `.change_password(user, old, new) -> None`. Deps: `get_current_user(...) -> User`, `require_role(*roles) -> Callable`. Schemas: `LoginIn{email,password}`, `TokenPair{access_token, refresh_token, token_type="bearer", force_password_reset}`, `ChangePasswordIn{old_password,new_password}`. Routes: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/change-password`.

- [ ] **Step 1: Write `backend/app/schemas/auth.py`**

```python
from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    force_password_reset: bool = False


class RefreshIn(BaseModel):
    refresh_token: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str
```

- [ ] **Step 2: Write `backend/app/services/auth_service.py`**

```python
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
```

- [ ] **Step 3: Write `backend/app/api/deps.py`**

```python
import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.database import get_db
from app.models.user import User


def get_current_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = security.decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_role(*roles: str) -> Callable[[User], User]:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user
    return checker
```

- [ ] **Step 4: Write `backend/app/api/auth.py`**

```python
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import security
from app.database import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordIn, LoginIn, RefreshIn, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(body: LoginIn, db: Session = Depends(get_db)):
    from app.services.auth_service import AuthService

    pair = AuthService(db).login(body.email, body.password)
    if pair is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return pair


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    try:
        payload = security.decode_token(body.refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return TokenPair(
        access_token=security.create_access_token(sub=str(user.id), role=user.role.value),
        refresh_token=security.create_refresh_token(sub=str(user.id)),
        force_password_reset=user.force_password_reset,
    )


@router.post("/change-password", status_code=204)
def change_password(
    body: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.auth_service import AuthService

    ok = AuthService(db).change_password(user, body.old_password, body.new_password)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Old password incorrect")
```

- [ ] **Step 5: Mount router in `backend/app/main.py`**

Add after CORS middleware:

```python
from app.api.auth import router as auth_router

app.include_router(auth_router)
```

- [ ] **Step 6: Write integration test `backend/tests/test_auth_api.py`**

```python
# ponytail: hits the real Postgres test DB (alembic upgrade head must have run).
import uuid

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)


def _mk_user(email, role, pw="pw12345"):
    db = SessionLocal()
    u = User(id=uuid.uuid4(), email=email, password_hash=security.hash_password(pw), role=role)
    db.add(u)
    db.commit()
    db.close()


def test_login_and_rbac_flow():
    email = f"admin-{uuid.uuid4().hex[:8]}@x.io"
    _mk_user(email, Role.admin)

    r = client.post("/auth/login", json={"email": email, "password": "pw12345"})
    assert r.status_code == 200
    assert r.json()["access_token"]

    bad = client.post("/auth/login", json={"email": email, "password": "nope"})
    assert bad.status_code == 401
```

- [ ] **Step 7: Run tests**

Run: `cd backend && alembic upgrade head && pytest tests/test_auth_api.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/auth_service.py backend/app/schemas backend/app/api backend/app/main.py backend/tests/test_auth_api.py
git commit -m "feat(p0): auth service, JWT login/refresh, RBAC deps"
```

---

### Task 6: Seed admin + admin-only smoke endpoint (integration verify)

**Files:**
- Create: `backend/app/seed.py`
- Create: `backend/app/api/admin.py`
- Modify: `backend/app/main.py` (mount admin router)
- Test: `backend/tests/test_admin_rbac.py`

**Interfaces:**
- Consumes: `require_role`, `UserRepository`, `security.hash_password`, `settings.first_admin_*`.
- Produces: `seed_admin()` idempotent. Route `GET /admin/ping` → `{"pong": true}` gated by `require_role("admin")`.

- [ ] **Step 1: Write `backend/app/seed.py`**

```python
from app.database import SessionLocal
from app.config import settings
from app.core.security import hash_password
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
```

- [ ] **Step 2: Write `backend/app/api/admin.py`**

```python
from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping(user: User = Depends(require_role("admin"))):
    return {"pong": True}
```

- [ ] **Step 3: Mount admin router in `backend/app/main.py`**

```python
from app.api.admin import router as admin_router

app.include_router(admin_router)
```

- [ ] **Step 4: Write `backend/tests/test_admin_rbac.py`**

```python
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
```

- [ ] **Step 5: Run tests**

Run: `cd backend && alembic upgrade head && pytest tests/test_admin_rbac.py -v`
Expected: PASS (admin 200, teacher 403, anon 401).

- [ ] **Step 6: Full-stack smoke via Docker Compose**

Run: `docker compose up --build -d`
Then:
```bash
curl -s localhost:8000/health          # {"status":"ok"}
curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@smartcampus.local","password":"ChangeMe123!"}'   # returns tokens
```
Expected: health ok, login returns access+refresh + `force_password_reset: true`.

- [ ] **Step 7: Commit**

```bash
git add backend/app/seed.py backend/app/api/admin.py backend/app/main.py backend/tests/test_admin_rbac.py
git commit -m "feat(p0): admin seed + admin-only ping + rbac integration test"
```

---

### Task 7: AttendanceProvider abstraction + registry

**Files:**
- Create: `backend/app/core/providers/__init__.py`
- Create: `backend/app/core/providers/attendance.py`
- Test: `backend/tests/test_provider_registry.py`

**Interfaces:**
- Produces: abstract `AttendanceProvider` with `method: str` and `validate_and_mark(db, payload) -> Attendance` (abstract). `register_provider(provider)` and `get_provider(method) -> AttendanceProvider`. Module-level `PROVIDERS: dict[str, AttendanceProvider]`. No QR impl here (Phase 2).

- [ ] **Step 1: Write failing test `backend/tests/test_provider_registry.py`**

```python
import pytest

from app.core.providers import attendance as prov


class _Fake(prov.AttendanceProvider):
    method = "QR"

    def validate_and_mark(self, db, payload):
        return "marked"


def test_register_and_get():
    p = _Fake()
    prov.register_provider(p)
    assert prov.get_provider("QR") is p


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        prov.get_provider("FACE")


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        prov.AttendanceProvider()
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_provider_registry.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Write `backend/app/core/providers/attendance.py`**

```python
from abc import ABC, abstractmethod

# ponytail: plain registry dict, no factory class. A provider registers itself; QR arrives in Phase 2.
PROVIDERS: dict[str, "AttendanceProvider"] = {}


class AttendanceProvider(ABC):
    method: str  # "QR" | "FACE" | "RFID" | "NFC"

    @abstractmethod
    def validate_and_mark(self, db, payload):
        """Validate the attendance payload and persist an Attendance row. Returns it."""
        ...


def register_provider(provider: "AttendanceProvider") -> None:
    PROVIDERS[provider.method] = provider


def get_provider(method: str) -> "AttendanceProvider":
    return PROVIDERS[method]
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_provider_registry.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/providers backend/tests/test_provider_registry.py
git commit -m "feat(p0): AttendanceProvider abstraction + registry"
```

---

### Task 8: Next.js PWA scaffold

**Files:**
- Create: `frontend/` (Next.js app via create-next-app)
- Create: `frontend/public/manifest.webmanifest`
- Modify: `frontend/src/app/layout.tsx` (link manifest)
- Modify: `frontend/Dockerfile`
- Modify: `docker-compose.yml` (add frontend service)

**Interfaces:**
- Produces: a running Next.js dev server on :3000 with a PWA manifest linked. No app features yet (built in P2).

- [ ] **Step 1: Scaffold**

Run: `npx create-next-app@latest frontend --typescript --tailwind --app --eslint --src-dir --use-npm --no-turbopack`
(Accept defaults for import alias.)

- [ ] **Step 2: Write `frontend/public/manifest.webmanifest`**

```json
{
  "name": "SmartCampus Attendance",
  "short_name": "SmartCampus",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0b0b0f",
  "theme_color": "#0b0b0f",
  "icons": []
}
```

- [ ] **Step 3: Link manifest in `frontend/src/app/layout.tsx`**

Add to the exported `metadata` object:

```typescript
export const metadata = {
  title: "SmartCampus Attendance",
  manifest: "/manifest.webmanifest",
};
```

- [ ] **Step 4: Write `frontend/Dockerfile`**

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

- [ ] **Step 5: Add frontend service to `docker-compose.yml`**

```yaml
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

- [ ] **Step 6: Verify**

Run: `docker compose up --build`
Open `http://localhost:3000` → Next.js page loads. DevTools → Application → Manifest shows "SmartCampus Attendance".

- [ ] **Step 7: Commit**

```bash
git add frontend docker-compose.yml
git commit -m "feat(p0): next.js pwa scaffold + manifest + compose service"
```

---

## Phase 0 Done Criteria
- `docker compose up --build` brings up db + backend + frontend.
- Alembic migrations apply; all 14 tables (incl. 3 face placeholders) exist.
- Seeded admin logs in; `/admin/ping` returns 200 for admin, 403 for teacher, 401 anon.
- `pytest` green in `backend/`.
- Update `phases.md` STATUS: Phase 0 → COMPLETED; log any cut corners in `DECISIONS.md`.
