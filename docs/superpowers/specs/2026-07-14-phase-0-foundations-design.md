# Phase 0 — Foundations — Design Spec

Date: 2026-07-14
Status: Approved (design gate passed)
Part of: SmartCampus University Attendance V1 (see `phases.md`)

## Goal
A running, authenticated skeleton: Docker Compose brings up Postgres + FastAPI (+ Next.js
scaffold), Alembic applies the foundational schema, a seeded admin can log in and receive a
JWT, and RBAC gates admin-only routes. Everything later (teachers, QR attendance, dashboard)
builds on this without redesign.

## Non-goals (this phase)
Teacher CRUD/import (P1), QR/session logic (P2), dashboard/audit/network gating (P3),
device intelligence/quarantine (P4), reports (P5), real PWA UI.

## Repo layout
```
backend/
  app/
    main.py            # FastAPI app, CORS (LAN origins), router mount, /health
    config.py          # Pydantic Settings (env-driven)
    database.py        # SQLAlchemy engine + SessionLocal + Base + get_db
    models/            # ORM models grouped by domain
    schemas/           # Pydantic request/response
    repositories/      # base.py + user_repo.py
    services/          # base.py + auth_service.py
    api/               # auth.py router + deps.py (RBAC dependencies)
    core/              # security.py (JWT + hashing), rbac.py,
                       #   providers/attendance.py (abstract AttendanceProvider + registry)
    seed.py            # create first admin
  alembic/             # env.py + versions/
  alembic.ini
  requirements.txt
  Dockerfile
frontend/              # Next.js PWA scaffold only
docker-compose.yml
.env.example
README.md
```

## Data model (Phase 0 Alembic migration)
UUID primary keys everywhere; `created_at`, `updated_at` timestamps on all tables.

- **users**: email (unique), password_hash, role enum(`admin|teacher|kiosk`), is_active bool,
  force_password_reset bool
- **faculties**: name (unique)
- **departments**: name, faculty_id → faculties (unique per faculty)
- **teachers**: user_id → users, faculty_id, department_id, employee_id (unique),
  full_name, dob (date), designation, email
- **attendance_kiosks**: name, user_id → users (kiosk role), location, is_active
- **devices**: fingerprint (unique), first_seen, last_seen, user_agent
- **attendance_sessions**: session_code (`ATT-YYYY-MM-DD`, unique), session_date (unique), is_active
- **attendance**: teacher_id, session_id, status enum(`present|absent`),
  attendance_method enum(`QR|FACE|RFID|NFC`, default QR), device_id, marked_at.
  Unique constraint (teacher_id, session_id).
- **qr_tokens**: session_id, token (unique), nonce, issued_at, expires_at, used_at (nullable), kiosk_id
- **audit_logs**: actor_user_id, action, entity, detail (jsonb), ip, created_at — append-only
- **system_settings**: key (unique), value (jsonb)
- **Empty placeholders** (columns defined, never written in V1):
  face_profiles, face_embeddings, face_verification_logs

## Auth
- `POST /auth/login` → `{access_token, refresh_token}`. Access 15m, refresh 7d. Argon2 hashing.
- `POST /auth/refresh` → new access token.
- `POST /auth/change-password` → verifies old, sets new, clears force_password_reset.
- RBAC: `require_role("admin")` FastAPI dependency reads role claim from JWT. 403 on mismatch.
- ponytail: no refresh-token rotation/blacklist yet (P3 with audit).

## AttendanceProvider abstraction
`core/providers/attendance.py`: abstract base with `validate_and_mark(...)` +
a module-level registry dict `PROVIDERS = {}` keyed by method string. Only defined here;
`QRProvider` registered in P2. No factory class.

## Repository + Service base classes
`repositories/base.py`: generic get/list/create/update over a model + session.
`services/base.py`: holds a repo, wraps business logic. `auth_service.py` is the first concrete one.

## Deployment
`docker-compose.yml`: services `db` (postgres:16, named volume, healthcheck),
`backend` (depends_on db healthy; runs `alembic upgrade head` then uvicorn), `frontend`.
`.env.example` documents all vars. CORS restricted to LAN origins from settings.

## Verification (must pass to call P0 done)
1. `docker compose up` → db healthy, migrations apply cleanly, backend serves `/health` 200.
2. `python -m app.seed` (or entrypoint) creates admin idempotently.
3. `POST /auth/login` with admin creds → 200 + JWT.
4. Admin-only smoke endpoint → 200 with admin JWT, 403 with teacher JWT, 401 without token.
5. One runnable check: `backend/tests/test_auth.py` asserting hash round-trip + RBAC 403 path.

## Deliberate corner-cuts (logged in DECISIONS.md)
Sync SQLAlchemy; no token blacklist; frontend scaffold-only; deferred tables not created.
