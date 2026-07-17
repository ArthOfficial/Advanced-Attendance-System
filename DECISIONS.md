# Decisions, Deferrals & Between-Phase Requests — Log

Append-only running log. Newest at bottom. Every non-obvious decision, deferred item,
cut corner, and user request that lands between phases goes here so nothing is lost.

Format: `YYYY-MM-DD | PHASE | TYPE | note`
TYPE ∈ decision · deferral · cut-corner · user-request · assumption · open-question

---

- 2026-07-14 | P0 | decision | Build phases 0→3 now; phases 4 (device intel + quarantine) & 5 (reports) DEFERRED.
- 2026-07-14 | P0 | decision | Stack pinned by user: FastAPI, Postgres, SQLAlchemy ORM, Alembic, Pydantic, UUID PKs, JWT+RBAC (admin/teacher/kiosk), Docker Compose primary, Repository+Service, AttendanceProvider abstraction.
- 2026-07-14 | P0 | cut-corner | Sync SQLAlchemy (not async) until load demands. Upgrade path: swap to async engine + async sessions.
- 2026-07-14 | P0 | cut-corner | No refresh-token rotation/blacklist table in P0; add in P3 alongside audit logging.
- 2026-07-14 | P0 | decision | Frontend is scaffold-only in P0; real PWA UI (scanner + kiosk) built in P2.
- 2026-07-14 | P0 | decision | AttendanceProvider = abstract base + simple registry dict keyed by method string. No factory class (YAGNI).
- 2026-07-14 | P0 | deferral | Tables device_ownership, quarantine_cases, reports NOT created in P0 migration — added in their own phases.
- 2026-07-14 | P0 | decision | face_profiles / face_embeddings / face_verification_logs created EMPTY in P0 (spec-required placeholders, never written).
- 2026-07-14 | P0 | open-question | Repo is not a git repo yet (env reported git but shell says no). Not running `git init` unless user asks.
- 2026-07-14 | P0 | user-request | Maintain working.md, phases.md status, and this DECISIONS.md continuously. Use superpowers + claude-mem. Rules mirrored into CLAUDE.md.
- 2026-07-14 | P0 | decision | Phase 0 impl plan written: docs/superpowers/plans/2026-07-14-phase-0-foundations.md (8 TDD tasks).
- 2026-07-14 | P0 | open-question | Plan tasks end in `git commit` but repo has no `.git`. Executor must `git init` before Task 1 (or we drop the commit steps). Pending user choice of exec mode.
- 2026-07-14 | P0 | cut-corner | test_user_repo uses SQLite in-memory for the User table only; UUID/JSONB-heavy models tested against Postgres in integration tests (Tasks 5,6).
- 2026-07-14 | P0 | decision | test_user_repo actually runs against Postgres (not SQLite) — postgresql.UUID/JSONB don't compile on SQLite. All DB tests need Postgres up + `alembic upgrade head`.
- 2026-07-14 | P0 | bugfix | LoginIn.email changed EmailStr→str. email-validator rejects reserved TLDs like `.local`, which LAN deployments use (admin@smartcampus.local). Emails validated at creation (P1). Regression test added.
- 2026-07-14 | P0 | decision | AuthService imported at module top in api/auth.py (plan had lazy inline import); no circular-import risk, cleaner.
- 2026-07-14 | P0 | decision | Docker Desktop was not running; launched it. Local pytest runs need DATABASE_URL=...@localhost:5432 (compose maps 5432→host); container uses @db:5432.
- 2026-07-14 | P0 | decision | Postgres 5432 published to host in docker-compose.yml so local alembic/pytest can reach the DB.
- 2026-07-14 | P0 | assumption | Git line-ending warnings (LF→CRLF) are cosmetic on Windows; not adding a .gitattributes unless it causes trouble.
- 2026-07-14 | P0 | note | frontend/AGENTS.md (from create-next-app) warns this Next.js version has breaking changes vs training data — read node_modules/next/dist/docs before writing frontend code in P2.
- 2026-07-14 | P1 | user-request | Login = Employee ID + DOB password. Email optional for teachers (nullable users.email). Admin/kiosk still log in by email — login identifier tries employee_id then email.
- 2026-07-14 | P1 | user-request | Import duplicates: two-step preview→commit. Preview shows every duplicate with full details (id, department, everything); admin chooses override / skip / stop. Override never touches passwords.
- 2026-07-14 | P1 | user-request | Unknown faculty/department in import → reject row; admin pre-creates.
- 2026-07-14 | P1 | decision | Import preview cached in new `import_batches` table (JSONB, 1h expiry) so commit survives restarts; no dangling state.
- 2026-07-14 | P1 | cut-corner | No admin frontend in P1 — admin uses FastAPI /docs until P3 dashboard.
- 2026-07-14 | P1 | note | claude-mem plugin DB exists but has 0 observations/summaries — passive memory never captured anything. Compensating: repo trackers + Claude Code file-based memory (MEMORY.md) updated instead.
- 2026-07-14 | P1 | bugfix | Import tests: fixture employee IDs/emails were static → unique-violation across runs. Tests now tag IDs+emails per run. Lesson: fixture data must be run-unique when tests hit a shared Postgres.
- 2026-07-14 | P1 | cut-corner | XLS legacy format untested (needs xlrd); XLSX+CSV covered. Add xlrd only if a real sheet demands it.
- 2026-07-14 | P1 | note | Docker Desktop stops between sessions — restart it before running DB tests.
- 2026-07-14 | P1 | decision | Phase 1 COMPLETE. V1 has NO UI yet besides Next.js placeholder — admin works via http://localhost:8000/docs (Swagger). Real UI: kiosk+scanner in P2, admin dashboard in P3.
- 2026-07-15 | P2 | decision | Phase 2 COMPLETE. Kiosk polls /kiosk/qr every 30s (no websocket). Scanner: BarcodeDetector native + jsQR fallback + paste-code fallback (camera-less testing).
- 2026-07-15 | P2 | cut-corner | No qr_tokens purge job (rows tiny; add in P5 if needed). No device fingerprinting (P4). QR payload = plain JSON {payload,sig} string.
- 2026-07-15 | P2 | decision | Kiosk usernames are kiosk-<hex>@kiosk.local in users.email; disabling kiosk disables its user login too.
- 2026-07-16 | P3 | bugfix | test_provider_registry fake provider registered under "QR", clobbering the real QRProvider in the shared registry → scan tests got str "marked". Fake now uses method "FAKE". Lesson: module-level registries are shared across the test session.
- 2026-07-16 | P3 | decision | Network validation: SystemSetting "allowed_networks" {enabled,cidrs}. Loopback always allowed; unparseable client IP fail-open (ponytail — testclient/odd proxies). Only /attendance/scan enforced in V1.
- 2026-07-16 | P3 | user-request | User forgot admin password → reset directly in DB to ChangeMe123!. No forgot-password flow in V1 (admin resets via DB or /docs).
- 2026-07-16 | P3 | decision | Phase 3 COMPLETE. Admin UI at /admin (dashboard, academic CRUD, teachers+import wizard, kiosks, audit, network). /docs kept as power-user fallback.
- 2026-07-16 | P3 | cut-corner | Admin UI uses prompt()/confirm() for rename/delete — no modal components. Upgrade if UX matters.
- 2026-07-16 | P3 | decision | V1 scope (phases 0→3) done. P4 (device intel/quarantine) & P5 (reports) remain deferred per original plan.
- 2026-07-16 | P5 | decision | Built P5 (reports) lean after user asked to keep building post-V1. P4 stays deferred — phases.md explicitly gates it on confirmed need (false-positive lockout risk).
- 2026-07-16 | P5 | cut-corner | CSV via stdlib csv module, not pandas/openpyxl. XLSX/PDF exports on demand later. Rollups computed in Python, fine for hundreds of teachers.
- 2026-07-16 | P5 | decision | Report percent = present / (sessions_in_range × teachers_in_group). Teachers created mid-range are counted against all sessions in range (no hire-date proration).
- 2026-07-16 | ops | user-request | Wiped all test-generated accounts/data from dev DB; kept 1 admin, created 3 named test teachers + 1 kiosk. Test-account teachers have force_password_reset=False (demo convenience — real imports still force reset).
- 2026-07-16 | bugfix | api() now redirects to /login on 401 instead of surfacing "HTTP 401" — expired access tokens (15 min) were leaving pages stuck.
- 2026-07-16 | bugfix | Phones couldn't use the app: NEXT_PUBLIC_API_URL default localhost:8000 + CORS localhost-only. API base now derived from window.location.hostname; CORS regex allows any http origin on :3000 (fine — local-network app, real gate is JWT + optional CIDR allowlist).
- 2026-07-16 | decision | "Keep me logged in" = storage choice (localStorage vs sessionStorage) + silent refresh-token retry on 401. No server-side session table (ponytail).
- 2026-07-16 | decision | has_children is intentional (block deleting faculty with departments / department with teachers); only the message was made human-readable. No cascade delete.
- 2026-07-17 | ui | user-request | Deletes are now cascading behind an explicit confirm popup: faculty→(departments+teachers), department→(teachers, faculty kept), teacher→type-"confirm". Backend still 409s without ?force=true, so nothing cascades by accident via API.
- 2026-07-17 | decision | Teacher cascade keeps audit_logs rows (immutable history) — actor_user_id is nulled instead of deleting rows.
