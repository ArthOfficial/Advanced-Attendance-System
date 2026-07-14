# Phase 1 — Academic Structure + Teacher Management — Design Spec

Date: 2026-07-14
Status: Approved (design gate passed)
Part of: SmartCampus University Attendance V1 (see `phases.md`)

## Goal
Admins manage faculties/departments and create teachers (manually or via spreadsheet
import with a preview→commit flow). Teachers log in with **Employee ID + DOB password**
and must change the password on first login. Email is optional contact info.

## Non-goals (this phase)
QR/attendance logic (P2), dashboards/admin UI (P3), reports (P5). No frontend work —
admin uses FastAPI `/docs` until P3 (ponytail cut, logged).

## Auth change (modifies Phase 0 behavior)
- `LoginIn.email` → `LoginIn.identifier`: tried as **employee_id first** (teachers),
  then as **email** (admins/kiosks, who have no employee ID).
- `users.email` becomes **nullable** (teachers may have no email). New Alembic migration.
  Unique constraint kept (Postgres allows multiple NULLs).
- Teacher default password = DOB as `DDMMYYYY` (e.g. 15/08/1990 → `15081990`),
  `force_password_reset = true`. Change-password clears the flag (exists from P0).

## Academic CRUD (admin-only)
- `POST/GET/PATCH/DELETE /faculties` — name unique. DELETE with departments → 409.
- `POST/GET/PATCH/DELETE /departments` — requires existing `faculty_id`; (faculty_id, name)
  unique. DELETE with teachers → 409. GET list filterable by `faculty_id`.
- Thin routers → `AcademicService` → `FacultyRepository`/`DepartmentRepository`.

## Manual teacher creation (admin-only)
- `POST /teachers`: employee_id, full_name, dob (ISO date), faculty_id, department_id,
  designation (optional), email (optional).
- One transaction: create `users` row (email=teacher email or NULL, password=DOB-derived,
  role=teacher, force_password_reset=true) + `teachers` row. Duplicate employee_id → 409.
  Department must belong to the given faculty → 422 otherwise.
- `GET /teachers` (admin list, filter by faculty_id/department_id, search by name/employee_id),
  `GET /teachers/{id}` (admin), `GET /me` (teacher: own profile + faculty/department names).

## Spreadsheet import (admin-only) — preview → commit
Formats: XLSX, XLS, CSV (Pandas + OpenPyXL). Expected columns (case-insensitive,
whitespace-trimmed): `Employee ID, Full Name, DOB, Faculty, Department, Designation, Email`.

**Step 1 — `POST /teachers/import/preview`** (multipart file). Parses and validates every
row; **writes no teacher/user rows**. Validation per row:
- required: employee_id, full_name, dob, faculty, department
- dob parseable as `DD/MM/YYYY` (also accepts `DD-MM-YYYY` and Excel date cells)
- faculty + department must exist (by case-insensitive name) and match → else rejected
  ("unknown faculty/department" — admin pre-creates, then re-uploads)
- duplicate employee_id within the file → later rows rejected ("duplicate in file")
- employee_id already in DB → classified as **duplicate**, with full incoming row AND
  existing record (name, faculty, department, designation, email) so admin can compare.

Response: `{import_id, valid: [...], duplicates: [{row, existing}], rejected: [{row, reason}],
counts}`. The parsed batch is stored in an `import_batches` table (JSONB payload,
expires_at = +1h) so commit survives restarts and nothing dangles forever.

**Step 2 — `POST /teachers/import/commit`** `{import_id, duplicate_action: "skip"|"override"}`:
- `skip`: create valid rows only; duplicates untouched.
- `override`: also update existing duplicates' profile fields (full_name, faculty,
  department, designation, email, dob). **Passwords never touched on override.**
- No commit call (or expired/consumed import_id → 404/410): nothing is ever written.
Returns final summary `{created, updated, skipped, rejected}`.

## New table (Alembic migration, same revision as users.email nullable)
- `import_batches`: id (UUID), payload (JSONB), created_by (fk users), expires_at,
  consumed_at (nullable), timestamps.

## Audit logging
`audit_logs` rows for: faculty/department create/update/delete, teacher create,
import commit (with counts), password change, login success/failure. Written via a tiny
`audit(db, actor_id, action, entity, detail, ip)` helper in `app/core/audit.py`.

## Testing
- Academic CRUD: create/list/409-on-delete-with-children, RBAC (teacher → 403).
- DOB→password derivation unit test (`15/08/1990` → `15081990`).
- Login with employee_id works; email login still works for admin; teacher without email works.
- Import: fixture CSV with valid + in-file-duplicate + DB-duplicate + unknown-department +
  bad-DOB rows → preview classifies correctly; commit skip vs override behave as specified;
  override never changes password_hash; expired/consumed import_id rejected.

## Deliberate corner-cuts (logged in DECISIONS.md)
No admin frontend (use /docs until P3). XLS legacy format via pandas/xlrd only if xlrd
installs cleanly, else document XLSX+CSV only. Login-failure audit rows only for
known-identifier failures (unknown identifiers logged without user id).
