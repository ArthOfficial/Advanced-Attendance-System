# TRANSFER GUIDE — SmartCampus University Attendance

This document explains how to hand this project over to a new person on a new laptop,
with the database exactly as it is right now. It is written for a **complete beginner**
— the new owner can paste this whole file into an AI assistant (ChatGPT / Claude / etc.)
and it will have everything it needs to guide them.

---

## 1. WHAT THIS PROJECT IS

A self-hosted, local-network **university teacher attendance system**:
- A kiosk screen shows a **QR code that changes every 30 seconds**.
- Teachers scan it with their phone (PWA web app) → marked **Present** for the day.
- Admin has a full dashboard: teachers, faculties/departments, spreadsheet import,
  kiosks, reports (CSV export), audit log, network (IP allowlist) settings.

**Tech stack** (all runs inside Docker, nothing needs manual installing except Docker):
| Part | Tech |
|---|---|
| Backend API | Python, FastAPI, SQLAlchemy, Alembic (port **8000**) |
| Database | PostgreSQL 16 (port **5432**, docker volume) |
| Frontend | Next.js + TypeScript + Tailwind PWA (port **3000**) |
| Auth | JWT tokens + roles: **admin / teacher / kiosk** |

GitHub repo: `https://github.com/ArthOfficial/Advanced-Attendance-System` (branch `main`)

Read these files in the repo root to understand everything:
- `phases.md` — the full roadmap and what is built (phases 0,1,2,3,5 done; 4 deferred)
- `working.md` — day-by-day log of everything that was done
- `DECISIONS.md` — every decision/corner-cut and why
- `CLAUDE.md` — project rules (keep those 3 files updated as you work!)

---

## 2. FOR THE CURRENT OWNER — WHAT TO GIVE YOUR FRIEND

Give him **two things**:

### A. The project folder (choose ONE way)
- **Easiest**: zip the whole project folder `AttendaceUnviersity/` and send it
  (USB / Google Drive). Before zipping you can delete these to shrink it —
  they are all regenerated automatically:
  - `frontend/node_modules/`  (huge, `npm install` recreates it)
  - `frontend/.next/`         (build output)
  - `backend/.venv/`          (Python virtualenv — Docker doesn't need it)
  - `backend/**/__pycache__/`
- **Or**: he clones from GitHub: `git clone https://github.com/ArthOfficial/Advanced-Attendance-System.git`
  (then he only needs the database file from you, see B).

### B. The database, exactly as it is now
The live data lives in a Docker **volume**, NOT in the project folder — zipping the
folder does NOT include the data. A snapshot has already been created:

- **`db_backup.sql`** (in the project root) — contains all current users, teachers,
  faculties, kiosks, attendance history, settings.

If you want a FRESHER snapshot right before handing over, run this in the project folder:
```
docker compose exec -T db pg_dump -U smartcampus smartcampus > db_backup.sql
```
Make sure `db_backup.sql` is inside the zip you send.

### C. Tell him the passwords (also listed in section 5)
That's it from your side.

---

## 3. FOR THE NEW OWNER — WHAT TO INSTALL ON YOUR LAPTOP

You only **need** #1. Install #2–#4 only if you want to write code, not just run the app.

1. **Docker Desktop** (REQUIRED — runs the whole app)
   - Download: https://www.docker.com/products/docker-desktop/
   - Windows: it may ask to enable **WSL 2** — say yes and follow its instructions.
   - After installing, START Docker Desktop and wait until it says "running".
2. *(optional, for coding)* **Git** — https://git-scm.com/downloads
3. *(optional, for frontend coding)* **Node.js 20+** — https://nodejs.org
4. *(optional, for backend coding)* **Python 3.12+** — https://python.org

Minimum laptop: any 64-bit machine with 8 GB RAM and ~10 GB free disk.

---

## 4. FOR THE NEW OWNER — SETUP, STEP BY STEP

1. Unzip the project folder anywhere (e.g. `C:\Projects\AttendaceUnviersity`).
2. Open a terminal **in that folder** (Windows: right-click → "Open in Terminal").
3. Start everything:
   ```
   docker compose up -d --build
   ```
   First time takes several minutes (downloads Postgres, builds backend+frontend).
4. **Restore the database snapshot** (do this ONCE, right after the first start):
   ```
   docker compose exec -T db psql -U smartcampus -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" smartcampus
   docker compose exec -T db psql -U smartcampus smartcampus < db_backup.sql
   ```
   (Skip this if you're fine starting with an empty system — then instead run
   `docker compose exec backend python -m app.seed` to create just the admin account.)
5. Open **http://localhost:3000** → you should see the login page. Done.

### Daily use afterwards
- Start:  `docker compose up -d`   (or just start Docker Desktop — containers restart)
- Stop:   `docker compose down`
- Logs:   `docker compose logs -f backend`
- After changing code: `docker compose up -d --build`

### Using it from phones (the whole point!)
- Find the laptop's LAN IP: `ipconfig` → e.g. `192.168.1.42`
- Phone (same Wi-Fi) opens `http://192.168.1.42:3000` — it just works
  (the app auto-detects the host; no config needed).
- If the phone can't reach it: allow ports **3000** and **8000** through Windows
  Firewall (Windows Security → Firewall → Advanced → Inbound Rules → New Rule → Port).

---

## 5. LOGINS (with the restored database)

| Role | Login | Password | Lands on |
|---|---|---|---|
| Admin | `admin@smartcampus.local` | `ChangeMe123!` | /admin dashboard |
| Teacher | `T001` (Alice Kumar) | `01011990` | /me |
| Teacher | `T002` (Bob Sharma) | `15051985` | /me |
| Teacher | `T003` (Carol Singh) | `31121992` | /me |
| Kiosk | `kiosk1@kiosk.local` | `Kiosk123!` | /kiosk QR screen |

Rules to know:
- Teachers log in with **Employee ID or email**; a new teacher's first password is
  their **date of birth as DDMMYYYY** and they must change it at first login.
- Kiosk accounts are created by the admin (Kiosks page shows the password ONCE).
- API docs (Swagger): http://localhost:8000/docs — full API playground.

---

## 6. PROJECT LAYOUT (for the AI helping the new owner)

```
docker-compose.yml        # db + backend + frontend — the whole deployment
db_backup.sql             # database snapshot (restore per section 4.4)
backend/
  app/api/                # FastAPI routers: auth, admin (stats/audit/reports/network),
                          # academic, teachers, imports, kiosks, kiosk_qr, attendance
  app/services/           # business logic (session, teacher, import, academic)
  app/repositories/       # DB access layer
  app/models/             # SQLAlchemy models (UUID pks)
  app/core/               # security (JWT/argon2), qr (HMAC), providers (QR), audit
  alembic/                # migrations — run automatically on container start
  tests/                  # pytest suite (34 tests) — uses smartcampus_test DB
frontend/
  src/app/                # login, change-password, me, scan, kiosk, admin/* pages
  src/lib/api.ts          # API wrapper: auto host detection, token refresh, 401 handling
  src/components/         # ConfirmDeleteModal etc.
phases.md / working.md / DECISIONS.md / CLAUDE.md   # project brain — READ THESE
```

### Running backend tests (optional, needs local Python)
```
cd backend
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
docker compose exec -T db psql -U smartcampus -c "CREATE DATABASE smartcampus_test"
.venv\Scripts\python -m alembic upgrade head   (with DATABASE_URL pointing at smartcampus_test)
.venv\Scripts\python -m pytest tests/ -q       # tests auto-target smartcampus_test (tests/conftest.py)
```

---

## 7. TROUBLESHOOTING (most common first)

| Problem | Fix |
|---|---|
| `docker compose` says cannot connect | Docker Desktop isn't running — start it, wait, retry |
| Port already in use | Something on 3000/8000/5432 — close it or edit ports in docker-compose.yml |
| Login button does nothing on phone | Use the laptop's IP (not localhost) + firewall ports 3000/8000 |
| "You must be connected to the University Network" on scan | Admin → Network page → disable the restriction or add your Wi-Fi subnet (e.g. `192.168.0.0/16`) |
| Forgot admin password | See section 8 |
| Frontend shows old UI after code change | `docker compose up -d --build frontend` |
| Everything broken, want fresh start | `docker compose down -v` (DELETES data!) → up → restore db_backup.sql again |

## 8. RESET ADMIN PASSWORD (if ever forgotten)
```
docker compose exec backend python -c "
from app.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
db = SessionLocal()
u = db.query(User).filter_by(email='admin@smartcampus.local').first()
u.password_hash = hash_password('ChangeMe123!'); u.force_password_reset = False
db.commit(); print('reset to ChangeMe123!')"
```

## 9. WHAT'S NOT BUILT (so nobody goes looking for it)
- Phase 4 (device fingerprinting + quarantine) — deliberately deferred.
- Face recognition — only empty placeholder tables exist, by design.
- Attendance statuses beyond Present/Absent, cloud anything — out of scope for V1.
- In progress at handover: multi-select (checkbox) bulk delete UI + admin UI polish
  (backend cascade-delete endpoints are done and tested).

Good luck! Start the containers, log in as admin, and click around — the UI covers
everything; http://localhost:8000/docs covers the rest.
