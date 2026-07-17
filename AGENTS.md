# AGENTS.md — SmartCampus University Attendance

Project rules for anyone (human or AI) working in this repo.

## Working rules — ALWAYS keep these files current
1. **`working.md`** — append what you are doing / did, with file names, as you go. Live worklog.
2. **`phases.md`** — the phased roadmap. Update the STATUS block when a phase starts/finishes.
3. **`DECISIONS.md`** — log EVERY non-obvious decision, deferral, cut corner, assumption,
   open question, and any user request that lands between phases. Nothing gets lost.

Update these BEFORE moving on, not at the end. If a request or decision would otherwise
"leave" (be forgotten between phases), it goes in `DECISIONS.md`.

## Process
- Use **superpowers** skills: brainstorm → writing-plans → executing-plans. Design gate before code.
- **Codex-mem** is active — memory builds passively; note durable project facts.
- Ponytail mode (lazy senior dev): simplest thing that works, stdlib/native first, shortest
  diff once the problem is understood. Mark deliberate corner-cuts with `# ponytail:` comments.
- Non-trivial logic leaves one runnable check behind (assert-based self-check or one test).

## Pinned stack (do not re-litigate)
FastAPI · PostgreSQL · SQLAlchemy ORM · Alembic · Pydantic · JWT + RBAC ·
Docker Compose (primary dev + deploy) · Next.js + TypeScript + Tailwind PWA.
UUID primary keys. Repository + Service architecture. `AttendanceProvider` abstraction
(QR only in V1; FACE/RFID/NFC addable without redesign).
Roles: **admin**, **teacher**, **kiosk**. Attendance statuses: **present / absent** only.

## Scope
V1 = Dynamic QR attendance, local-network, self-hosted, offline-capable.
Build phases 0→3 now. Phases 4 (device intel + quarantine) & 5 (reports) deferred.
No face recognition in V1 — only empty placeholder tables + unimplemented interfaces.
