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
