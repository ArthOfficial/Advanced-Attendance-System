Write all phases here while marking them completed in completed or completing or if anything working on that specific phase mark that

---

Start below from line 7

# SmartCampus University Attendance — Phased Roadmap

Version 1 focus: **Dynamic QR Attendance only.** Local-network, self-hosted, offline-capable.
Each phase is its own spec → plan → build cycle. Build order: **0 → 1 → 2 → 3** now; 4 & 5 deferred.

**Global stack (pinned):** FastAPI · PostgreSQL · SQLAlchemy ORM · Alembic · Pydantic ·
JWT + RBAC · Docker Compose (primary dev+deploy) · Next.js + TypeScript + Tailwind PWA.
UUID primary keys everywhere. Repository + Service architecture. `AttendanceProvider`
abstraction so FACE/RFID/NFC can be added later without refactor.

Roles: **Admin**, **Teacher**, **Attendance Kiosk**.

## STATUS
- Phase 0 — Foundations ............... COMPLETED (2026-07-14, 8 tasks, 9 tests green, compose smoke OK)
- Phase 1 — Academic + Teachers ....... COMPLETED (2026-07-14, 7 tasks, 24 tests green, compose smoke OK)
- Phase 2 — Core Attendance Loop ...... COMPLETED (2026-07-15, 29 tests green, E2E kiosk→QR→scan OK)
- Phase 3 — Admin + Audit + Network ... COMPLETED (2026-07-16, 31 tests green, admin UI live, compose smoke OK)
- Phase 4 — Device Intel + Quarantine . DEFERRED
- Phase 5 — Reports ................... COMPLETED (2026-07-16, lean: JSON+CSV rollups, 32 tests green, smoke OK)

---

## Phase 0 — Foundations  *(BUILD FIRST)*

Goal: a running, authenticated skeleton with the database and deploy story in place.

- Repo layout: `backend/` (FastAPI), `frontend/` (Next.js PWA), `docker-compose.yml`, `.env`.
- Docker Compose: `db` (Postgres), `backend`, `frontend`. Healthchecks, named volume for pgdata.
- Config via Pydantic Settings (`backend/app/config.py`), 12-factor env vars.
- SQLAlchemy base + session (sync — simpler; revisit only if load demands).
- Alembic wired up; first migration creates the **foundational schema**:
  - `users` (id, email, password_hash, role, is_active, force_password_reset, timestamps)
  - `faculties`, `departments`
  - `teachers` (fk users, fk faculty, fk department, employee_id, full_name, dob, designation, email)
  - `attendance_kiosks`, `devices`
  - `attendance_sessions`, `attendance`, `qr_tokens`
  - `audit_logs`, `system_settings`
  - **Empty placeholders** (spec-required, unused): `face_profiles`, `face_embeddings`, `face_verification_logs`
  - Deferred to their phases: `device_ownership`, `quarantine_cases`, `reports`.
- Auth: JWT (access + refresh), password hashing (argon2/bcrypt), RBAC dependency
  (`require_role(...)`), login + refresh + change-password endpoints, force-reset flow.
- `AttendanceProvider` abstract interface defined (only `QRProvider` implemented in Phase 2).
- Repository + Service base classes.
- Seed script: one admin account.
- Health endpoint, structured logging, CORS locked to LAN origins.

Deliverable: `docker compose up` → migrations run → admin can log in and get a JWT.

---

## Phase 1 — Academic Structure + Teacher Management

- CRUD: faculties, departments (admin only). Department belongs to faculty.
- Manual teacher creation (admin): full name, employee ID, DOB, faculty, department, designation, email.
  Auto-create linked `users` row; password = DOB as `DDMMYYYY`; `force_password_reset = true`.
- Spreadsheet import (XLSX/XLS/CSV) via Pandas/OpenPyXL:
  columns Employee ID, Full Name, DOB, Faculty, Department, Designation, Email.
  Validate, detect duplicates, auto-create accounts + DOB passwords, return import summary.
- Teacher self-service: view profile, change password (clears force-reset).
- Audit-log all create/import/password events.

---

## Phase 2 — Core Attendance Loop  *(the heart of V1)*

- Daily attendance session: auto-create one active session per day (`ATT-YYYY-MM-DD`).
  Date-change detection; recovery order: server date → last session date → last QR timestamp.
- Kiosk QR: rotates every 30s. Each QR = session id, unique token, issued-at, expiry (+30s),
  nonce, HMAC/ed25519 signature. Server-side validation only.
- `qr_tokens`: store issued tokens; enforce single-use (replay/screenshot reuse fails);
  expired tokens invalid immediately; token must belong to current active session.
- Teacher scan → validate → mark **Present** (statuses limited to Present/Absent).
  One mark per teacher per daily session; duplicate → "Attendance already recorded for today."
- `attendance.attendance_method = 'QR'` (column supports future FACE/RFID/NFC).
- All flows via `QRProvider` implementing `AttendanceProvider`.
- PWA QR scanner (camera) + kiosk QR display screen.

---

## Phase 3 — Admin Dashboard + Audit Log + Network Validation

- Admin dashboard tiles: total teachers, present/absent today, attendance %, active session,
  active kiosks. Search + faculty/department/date filters.
- Immutable, searchable audit log (append-only; no update/delete).
- University network validation: admin-configurable allowed IP ranges (192.168/10./172.16);
  attendance from outside fails with "You must be connected to the University Network."
  Optional (toggle in `system_settings`).

---

## Phase 4 — Device Ownership Intelligence + Quarantine  *(DEFERRED — reassess need)*

> Heaviest, riskiest, most speculative. Risk of false-positive lockouts of legitimate teachers.
> Not built until 0–3 are shipping and the need is confirmed.

- `device_ownership`: learn teacher↔device confidence over time.
- Conflict detection: attendance from a device owned by another teacher → block.
- `quarantine_cases` + admin quarantine dashboard (approve/reject/reset/force-logout/notes).

---

## Phase 5 — Reports  *(DEFERRED)*

- Daily / weekly / monthly / semester / faculty / department / teacher reports.
- Export CSV first (Pandas already there); XLSX (OpenPyXL) + PDF added on demand.
- University-wide / faculty / department / teacher rollups.

---

## Explicitly NOT in V1
Face recognition (only empty placeholder tables + unimplemented service interfaces).
Attendance statuses beyond Present/Absent. Cloud services.
