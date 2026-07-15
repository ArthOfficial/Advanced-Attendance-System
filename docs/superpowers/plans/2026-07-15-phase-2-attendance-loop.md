# Phase 2 — Core Attendance Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kiosk shows 30s-rotating HMAC-signed QR; teacher scans in PWA; server marks Present once per auto-created daily session; first real UI (login/kiosk/scan/me).

**Architecture:** SessionService auto-creates `ATT-YYYY-MM-DD`. Kiosk role fetches signed QR payloads from `/kiosk/qr`; QRProvider (registered in P0's PROVIDERS registry) validates signature/expiry/single-use/session and inserts attendance in one transaction. Next.js pages use a tiny JWT fetch wrapper.

**Tech Stack:** existing P0/P1 stack + `qrcode` + `jsqr` (npm).

## Global Constraints
- Tests: Postgres up + `alembic upgrade head`; `DATABASE_URL=postgresql+psycopg2://smartcampus:smartcampus@localhost:5432/smartcampus`; run via `./.venv/Scripts/python.exe -m pytest` from `backend/`.
- QR token TTL exactly 30s. Statuses `present|absent`; method `QR`. Roles `admin|teacher|kiosk`.
- HMAC-SHA256 over canonical JSON (`json.dumps(payload, sort_keys=True, separators=(",", ":"))`) keyed with `settings.jwt_secret`.
- Every scan outcome audited (`attendance.scan.*`). Ponytail cuts get `# ponytail:` + DECISIONS.md.
- Frontend: dark Tailwind, `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`), tokens in localStorage.

---

### Task 1: SessionService (daily session, idempotent)

**Files:** Create `backend/app/services/session_service.py`; Test `backend/tests/test_session_service.py`.

**Interfaces:** Produces `SessionService(db).get_or_create_today() -> AttendanceSession` (creates `ATT-YYYY-MM-DD`, deactivates older active ones; unique session_date ⇒ IntegrityError → re-select).

- [ ] Test:

```python
from app.database import SessionLocal
from app.services.session_service import SessionService


def test_get_or_create_today_idempotent():
    db = SessionLocal()
    try:
        s1 = SessionService(db).get_or_create_today()
        s2 = SessionService(db).get_or_create_today()
        assert s1.id == s2.id and s1.is_active
        assert s1.session_code == f"ATT-{s1.session_date.isoformat()}"
    finally:
        db.close()
```

- [ ] Impl:

```python
from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.models.attendance import AttendanceSession
from app.services.base import BaseService


class SessionService(BaseService):
    def get_or_create_today(self) -> AttendanceSession:
        today = datetime.now(timezone.utc).date()
        existing = (self.db.query(AttendanceSession)
                    .filter_by(session_date=today).first())
        if existing:
            if not existing.is_active:
                existing.is_active = True
                self.db.commit()
            return existing
        # ponytail: spec's clock-recovery — if server date is BEFORE the newest
        # session date (clock rolled back), reuse that newest session instead
        # of creating a "yesterday" duplicate.
        newest = (self.db.query(AttendanceSession)
                  .order_by(AttendanceSession.session_date.desc()).first())
        if newest and newest.session_date > today:
            return newest
        (self.db.query(AttendanceSession)
         .filter(AttendanceSession.is_active.is_(True))
         .update({"is_active": False}))
        try:
            s = AttendanceSession(session_code=f"ATT-{today.isoformat()}",
                                  session_date=today, is_active=True)
            self.db.add(s)
            self.db.commit()
            self.db.refresh(s)
            return s
        except IntegrityError:  # concurrent create
            self.db.rollback()
            return self.db.query(AttendanceSession).filter_by(session_date=today).one()
```

- [ ] Run test → PASS. Commit `feat(p2): daily session service`.

---

### Task 2: Kiosk management (admin) + kiosk repo

**Files:** Create `backend/app/api/kiosks.py`, `backend/app/schemas/kiosk.py`; Modify `backend/app/main.py`; Test `backend/tests/test_kiosks_api.py`.

**Interfaces:** `POST /kiosks {name, location?}` → 201 `{id, name, location, username, password}` (password shown once; username = `kiosk-<8hex>@kiosk.local` in users.email). `GET /kiosks` → list. `PATCH /kiosks/{id} {is_active}`. Kiosk logs in with that username/password via /auth/login.

- [ ] Schemas `backend/app/schemas/kiosk.py`:

```python
import uuid

from pydantic import BaseModel, ConfigDict


class KioskCreate(BaseModel):
    name: str
    location: str | None = None


class KioskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    location: str | None
    is_active: bool


class KioskCreated(KioskOut):
    username: str
    password: str


class KioskPatch(BaseModel):
    is_active: bool
```

- [ ] Router `backend/app/api/kiosks.py`:

```python
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_role
from app.core.audit import audit
from app.core.security import hash_password
from app.database import get_db
from app.models.infra import AttendanceKiosk
from app.models.user import Role, User
from app.schemas.kiosk import KioskCreate, KioskCreated, KioskOut, KioskPatch

router = APIRouter(prefix="/kiosks", tags=["kiosks"])


@router.post("", response_model=KioskCreated, status_code=201)
def create_kiosk(body: KioskCreate, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    username = f"kiosk-{secrets.token_hex(4)}@kiosk.local"
    password = secrets.token_urlsafe(8)
    ku = User(email=username, password_hash=hash_password(password), role=Role.kiosk)
    db.add(ku)
    db.flush()
    k = AttendanceKiosk(name=body.name, location=body.location, user_id=ku.id)
    db.add(k)
    db.commit()
    db.refresh(k)
    audit(db, user.id, "kiosk.created", entity=str(k.id), detail={"name": k.name})
    return KioskCreated(id=k.id, name=k.name, location=k.location, is_active=k.is_active,
                        username=username, password=password)


@router.get("", response_model=list[KioskOut])
def list_kiosks(user: User = Depends(require_role("admin")), db=Depends(get_db)):
    return db.query(AttendanceKiosk).all()


@router.patch("/{kid}", response_model=KioskOut)
def patch_kiosk(kid: uuid.UUID, body: KioskPatch, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    k = db.get(AttendanceKiosk, kid)
    if not k:
        raise HTTPException(404, "not_found")
    k.is_active = body.is_active
    ku = db.get(User, k.user_id)
    ku.is_active = body.is_active  # disabling kiosk kills its login too
    db.commit()
    audit(db, user.id, "kiosk.updated", entity=str(kid), detail={"is_active": body.is_active})
    return k
```

- [ ] Mount (`from app.api.kiosks import router as kiosks_router`; `app.include_router(kiosks_router)`).
- [ ] Test:

```python
import uuid

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)


def _admin_headers():
    db = SessionLocal()
    u = User(email=f"a-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=Role.admin)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='admin')}"}


def test_create_kiosk_password_logs_in():
    h = _admin_headers()
    r = client.post("/kiosks", json={"name": "Gate A", "location": "Main"}, headers=h)
    assert r.status_code == 201
    body = r.json()
    login = client.post("/auth/login", json={"identifier": body["username"],
                                             "password": body["password"]})
    assert login.status_code == 200

    # disable → login dies
    client.patch(f"/kiosks/{body['id']}", json={"is_active": False}, headers=h)
    login2 = client.post("/auth/login", json={"identifier": body["username"],
                                              "password": body["password"]})
    assert login2.status_code == 401
```

- [ ] Run → PASS. Commit `feat(p2): kiosk accounts admin API`.

---

### Task 3: QR issue endpoint + signing helper

**Files:** Create `backend/app/core/qr.py`, `backend/app/api/kiosk_qr.py`; Modify `backend/app/main.py`; Test `backend/tests/test_kiosk_qr.py`.

**Interfaces:** `sign_payload(payload: dict) -> str` and `verify_payload(payload: dict, sig: str) -> bool` (HMAC-SHA256 hex, canonical JSON, jwt_secret). `GET /kiosk/qr` (kiosk role) → `{payload: {sid, tok, iat, exp, nonce}, sig, session_code}`; creates qr_tokens row (expires +30s).

- [ ] `backend/app/core/qr.py`:

```python
import hashlib
import hmac
import json

from app.config import settings


def _canon(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def sign_payload(payload: dict) -> str:
    return hmac.new(settings.jwt_secret.encode(), _canon(payload), hashlib.sha256).hexdigest()


def verify_payload(payload: dict, sig: str) -> bool:
    return hmac.compare_digest(sign_payload(payload), sig)
```

- [ ] `backend/app/api/kiosk_qr.py`:

```python
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.core.qr import sign_payload
from app.database import get_db
from app.models.attendance import QRToken
from app.models.infra import AttendanceKiosk
from app.models.user import User
from app.services.session_service import SessionService

router = APIRouter(prefix="/kiosk", tags=["kiosk"])

QR_TTL_SECONDS = 30


@router.get("/qr")
def issue_qr(user: User = Depends(require_role("kiosk")), db=Depends(get_db)):
    session = SessionService(db).get_or_create_today()
    kiosk = db.query(AttendanceKiosk).filter_by(user_id=user.id).first()
    now = datetime.now(timezone.utc)
    tok = QRToken(
        session_id=session.id, kiosk_id=kiosk.id if kiosk else None,
        token=secrets.token_urlsafe(32), nonce=secrets.token_urlsafe(8),
        issued_at=now, expires_at=now + timedelta(seconds=QR_TTL_SECONDS),
    )
    db.add(tok)
    db.commit()
    payload = {"sid": str(session.id), "tok": tok.token,
               "iat": int(now.timestamp()), "exp": int(tok.expires_at.timestamp()),
               "nonce": tok.nonce}
    return {"payload": payload, "sig": sign_payload(payload),
            "session_code": session.session_code, "ttl": QR_TTL_SECONDS}
```

- [ ] Mount router. Test:

```python
import uuid

from fastapi.testclient import TestClient

from app.core import security
from app.core.qr import verify_payload
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)


def _headers(role: Role):
    db = SessionLocal()
    u = User(email=f"{role.value}-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=role)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role=role.value)}"}


def test_qr_issue_signed_and_rbac():
    r = client.get("/kiosk/qr", headers=_headers(Role.kiosk))
    assert r.status_code == 200
    b = r.json()
    assert verify_payload(b["payload"], b["sig"])
    assert b["payload"]["exp"] - b["payload"]["iat"] == 30
    # teacher blocked
    assert client.get("/kiosk/qr", headers=_headers(Role.teacher)).status_code == 403
```

- [ ] Run → PASS. Commit `feat(p2): signed 30s QR issue endpoint`.

---

### Task 4: QRProvider + scan endpoint + history

**Files:** Create `backend/app/core/providers/qr_provider.py`, `backend/app/api/attendance.py`, `backend/app/schemas/attendance.py`; Modify `backend/app/main.py`; Test `backend/tests/test_scan.py`.

**Interfaces:** `QRProvider.validate_and_mark(db, {payload, sig, teacher})` → Attendance row or raises `ScanError(code)` with code ∈ `bad_signature|unknown_token|expired|replayed|wrong_session|already_marked`. Registered `PROVIDERS["QR"]` at import (in main.py). Routes: `POST /attendance/scan {payload: dict, sig: str}` (teacher) → 200 `{status:"present", session_code, marked_at}`; errors → 400 (bad_signature/unknown_token/expired/replayed/wrong_session with detail message) / 409 already_marked "Attendance already recorded for today.". `GET /attendance/me` → `{records: [{date, status, method, marked_at}], present_days, total_sessions}`.

- [ ] `backend/app/core/providers/qr_provider.py`:

```python
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.providers.attendance import AttendanceProvider, register_provider
from app.core.qr import verify_payload
from app.models.attendance import (Attendance, AttendanceMethod,
                                   AttendanceStatus, QRToken)


class ScanError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class QRProvider(AttendanceProvider):
    method = "QR"

    def validate_and_mark(self, db, payload):
        data, sig, teacher = payload["payload"], payload["sig"], payload["teacher"]
        if not verify_payload(data, sig):
            raise ScanError("bad_signature")
        tok = db.query(QRToken).filter_by(token=data.get("tok")).first()
        if tok is None:
            raise ScanError("unknown_token")
        now = datetime.now(timezone.utc)
        if tok.used_at is not None:
            raise ScanError("replayed")
        if tok.expires_at < now:
            raise ScanError("expired")
        from app.services.session_service import SessionService
        active = SessionService(db).get_or_create_today()
        if tok.session_id != active.id:
            raise ScanError("wrong_session")
        tok.used_at = now
        att = Attendance(teacher_id=teacher.id, session_id=active.id,
                         status=AttendanceStatus.present,
                         attendance_method=AttendanceMethod.QR, marked_at=now)
        db.add(att)
        try:
            db.commit()  # one transaction: used_at + attendance row
        except IntegrityError:  # unique(teacher, session)
            db.rollback()
            raise ScanError("already_marked")
        db.refresh(att)
        return att


register_provider(QRProvider())
```

- [ ] `backend/app/schemas/attendance.py`:

```python
from datetime import date, datetime

from pydantic import BaseModel


class ScanIn(BaseModel):
    payload: dict
    sig: str


class ScanOut(BaseModel):
    status: str
    session_code: str
    marked_at: datetime


class AttendanceRecord(BaseModel):
    date: date
    status: str
    method: str
    marked_at: datetime | None


class MyAttendanceOut(BaseModel):
    records: list[AttendanceRecord]
    present_days: int
    total_sessions: int
```

- [ ] `backend/app/api/attendance.py`:

```python
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_role
from app.core.audit import audit
from app.core.providers.attendance import get_provider
from app.core.providers.qr_provider import ScanError
from app.database import get_db
from app.models.attendance import Attendance, AttendanceSession
from app.models.user import User
from app.repositories.teacher_repo import TeacherRepository
from app.schemas.attendance import (AttendanceRecord, MyAttendanceOut, ScanIn,
                                    ScanOut)

router = APIRouter(prefix="/attendance", tags=["attendance"])

_MSG = {
    "bad_signature": "Invalid QR code.",
    "unknown_token": "Invalid QR code.",
    "expired": "QR code expired. Scan the current code.",
    "replayed": "This QR code was already used.",
    "wrong_session": "QR code is not for today's session.",
}


@router.post("/scan", response_model=ScanOut)
def scan(body: ScanIn, user: User = Depends(require_role("teacher")), db=Depends(get_db)):
    teacher = TeacherRepository(db).get_by_user_id(user.id)
    if not teacher:
        raise HTTPException(404, "Teacher profile not found")
    try:
        att = get_provider("QR").validate_and_mark(
            db, {"payload": body.payload, "sig": body.sig, "teacher": teacher})
    except ScanError as e:
        db.rollback()
        audit(db, user.id, f"attendance.scan.{e.code}")
        if e.code == "already_marked":
            raise HTTPException(409, "Attendance already recorded for today.")
        raise HTTPException(400, _MSG[e.code])
    session = db.get(AttendanceSession, att.session_id)
    audit(db, user.id, "attendance.scan.success", entity=str(att.id))
    return ScanOut(status="present", session_code=session.session_code, marked_at=att.marked_at)


@router.get("/me", response_model=MyAttendanceOut)
def my_attendance(user: User = Depends(require_role("teacher")), db=Depends(get_db)):
    teacher = TeacherRepository(db).get_by_user_id(user.id)
    if not teacher:
        raise HTTPException(404, "Teacher profile not found")
    rows = (db.query(Attendance, AttendanceSession)
            .join(AttendanceSession, Attendance.session_id == AttendanceSession.id)
            .filter(Attendance.teacher_id == teacher.id)
            .order_by(AttendanceSession.session_date.desc()).all())
    records = [AttendanceRecord(date=s.session_date, status=a.status.value,
                                method=a.attendance_method.value, marked_at=a.marked_at)
               for a, s in rows]
    total = db.query(AttendanceSession).count()
    present = sum(1 for r in records if r.status == "present")
    return MyAttendanceOut(records=records, present_days=present, total_sessions=total)
```

- [ ] main.py: import qr_provider module (side-effect registration) + mount attendance router:

```python
import app.core.providers.qr_provider  # noqa: F401  registers QR provider
from app.api.attendance import router as attendance_router
app.include_router(attendance_router)
```

- [ ] Test `backend/tests/test_scan.py`:

```python
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.academic import Department, Faculty, Teacher
from app.models.attendance import QRToken
from app.models.user import Role, User

client = TestClient(app)


def _kiosk_headers():
    db = SessionLocal()
    u = User(email=f"k-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=Role.kiosk)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='kiosk')}"}


def _teacher_headers():
    db = SessionLocal()
    fac = Faculty(name=f"F-{uuid.uuid4().hex[:6]}"); db.add(fac); db.flush()
    dep = Department(name="D", faculty_id=fac.id); db.add(dep); db.flush()
    u = User(email=None, password_hash=security.hash_password("pw"), role=Role.teacher)
    db.add(u); db.flush()
    t = Teacher(user_id=u.id, faculty_id=fac.id, department_id=dep.id,
                employee_id=f"EMP{uuid.uuid4().hex[:8]}", full_name="T",
                dob=date(1990, 1, 1))
    db.add(t); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='teacher')}"}


def _qr():
    return client.get("/kiosk/qr", headers=_kiosk_headers()).json()


def test_scan_happy_then_duplicate_then_replay():
    th = _teacher_headers()
    qr = _qr()
    r = client.post("/attendance/scan", json={"payload": qr["payload"], "sig": qr["sig"]}, headers=th)
    assert r.status_code == 200 and r.json()["status"] == "present"

    # same teacher, fresh QR → already marked
    qr2 = _qr()
    r2 = client.post("/attendance/scan", json={"payload": qr2["payload"], "sig": qr2["sig"]}, headers=th)
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Attendance already recorded for today."

    # different teacher, REUSED token → replayed
    r3 = client.post("/attendance/scan", json={"payload": qr["payload"], "sig": qr["sig"]},
                     headers=_teacher_headers())
    assert r3.status_code == 400 and "already used" in r3.json()["detail"]


def test_scan_tampered_and_expired():
    th = _teacher_headers()
    qr = _qr()
    bad = dict(qr["payload"]); bad["tok"] = "forged"
    assert client.post("/attendance/scan", json={"payload": bad, "sig": qr["sig"]},
                       headers=th).status_code == 400

    # force-expire a fresh token in DB
    qr2 = _qr()
    db = SessionLocal()
    tok = db.query(QRToken).filter_by(token=qr2["payload"]["tok"]).one()
    tok.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit(); db.close()
    r = client.post("/attendance/scan", json={"payload": qr2["payload"], "sig": qr2["sig"]}, headers=th)
    assert r.status_code == 400 and "expired" in r.json()["detail"]


def test_kiosk_cannot_scan_and_history_works():
    kh = _kiosk_headers()
    qr = _qr()
    assert client.post("/attendance/scan", json={"payload": qr["payload"], "sig": qr["sig"]},
                       headers=kh).status_code == 403
    th = _teacher_headers()
    client.post("/attendance/scan", json={"payload": qr["payload"], "sig": qr["sig"]}, headers=th)
    me = client.get("/attendance/me", headers=th)
    assert me.status_code == 200 and me.json()["present_days"] == 1
```

- [ ] Run → PASS (note: expired-path edits DB directly; signature stays valid since sig covers payload, not row). Commit `feat(p2): QR provider, scan endpoint, attendance history`.

---

### Task 5: Frontend — auth lib + login + change-password

**Files:** Create `frontend/src/lib/api.ts`, `frontend/src/app/login/page.tsx`, `frontend/src/app/change-password/page.tsx`; Modify `frontend/src/app/page.tsx`.

**Interfaces:** `api(path, opts?)` fetch wrapper adding `Authorization` from localStorage `access_token`; `login()` stores `access_token`, `refresh_token`, `force_password_reset`, `role` (decoded from JWT payload). Home page redirects by role: teacher→/scan, kiosk→/kiosk, admin→backend /docs link + /me links.

- [ ] `frontend/src/lib/api.ts`:

```typescript
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function api(path: string, opts: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers ?? {}),
    },
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({})))?.detail ?? `HTTP ${res.status}`);
  return res.status === 204 ? null : res.json();
}

export function roleFromToken(): string | null {
  const t = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (!t) return null;
  try { return JSON.parse(atob(t.split(".")[1])).role ?? null; } catch { return null; }
}
```

- [ ] `frontend/src/app/login/page.tsx` (client component): identifier+password form, POST /auth/login, store tokens; if `force_password_reset` → router.push("/change-password") else role-home (`teacher→/scan, kiosk→/kiosk, admin→/`). Dark Tailwind card UI.

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { API, roleFromToken } from "@/lib/api";

export default function Login() {
  const [identifier, setId] = useState("");
  const [password, setPw] = useState("");
  const [err, setErr] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    const res = await fetch(`${API}/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password }),
    });
    if (!res.ok) { setErr("Invalid credentials"); return; }
    const b = await res.json();
    localStorage.setItem("access_token", b.access_token);
    localStorage.setItem("refresh_token", b.refresh_token);
    if (b.force_password_reset) { router.push("/change-password"); return; }
    const role = roleFromToken();
    router.push(role === "kiosk" ? "/kiosk" : role === "teacher" ? "/scan" : "/");
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-100">
      <form onSubmit={submit} className="w-80 space-y-4 rounded-2xl bg-zinc-900 p-8 shadow-xl">
        <h1 className="text-xl font-semibold">SmartCampus</h1>
        <input className="w-full rounded-lg bg-zinc-800 p-3 text-sm" placeholder="Employee ID or email"
               value={identifier} onChange={e => setId(e.target.value)} />
        <input className="w-full rounded-lg bg-zinc-800 p-3 text-sm" type="password" placeholder="Password"
               value={password} onChange={e => setPw(e.target.value)} />
        {err && <p className="text-sm text-red-400">{err}</p>}
        <button className="w-full rounded-lg bg-emerald-600 p-3 text-sm font-medium hover:bg-emerald-500">
          Sign in
        </button>
      </form>
    </main>
  );
}
```

- [ ] `/change-password/page.tsx`: old+new fields → `api("/auth/change-password", {method:"POST", body: JSON.stringify({old_password, new_password})})` → role-home. Same card styling.
- [ ] `page.tsx` (home): if no token → /login; else role links (teacher: Scan/My attendance; kiosk: Open kiosk; admin: link to `${API}/docs`). Keep it a simple client component.
- [ ] Verify: `npm run build` green. Commit `feat(p2): login + change-password + role home`.

---

### Task 6: Frontend — kiosk page

**Files:** Create `frontend/src/app/kiosk/page.tsx`; Modify `frontend/package.json` (add `qrcode`, `@types/qrcode`).

- [ ] `npm i qrcode && npm i -D @types/qrcode`
- [ ] Page (client): every 30s `api("/kiosk/qr")` → `QRCode.toCanvas(canvas, JSON.stringify({payload, sig}))`; countdown bar; session_code + kiosk name footer; fullscreen dark. On 401 → /login.

```tsx
"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { api } from "@/lib/api";

export default function Kiosk() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [code, setCode] = useState("");
  const [left, setLeft] = useState(30);

  const refresh = useCallback(async () => {
    try {
      const b = await api("/kiosk/qr");
      setCode(b.session_code);
      setLeft(b.ttl);
      if (canvasRef.current)
        QRCode.toCanvas(canvasRef.current, JSON.stringify({ payload: b.payload, sig: b.sig }),
                        { width: 420, margin: 1 });
    } catch { window.location.href = "/login"; }
  }, []);

  useEffect(() => {
    refresh();
    const qr = setInterval(refresh, 30_000);
    const tick = setInterval(() => setLeft(l => Math.max(0, l - 1)), 1_000);
    return () => { clearInterval(qr); clearInterval(tick); };
  }, [refresh]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 bg-zinc-950 text-zinc-100">
      <h1 className="text-2xl font-semibold">Scan to mark attendance</h1>
      <canvas ref={canvasRef} className="rounded-xl bg-white p-2" />
      <div className="h-1 w-[420px] overflow-hidden rounded bg-zinc-800">
        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${(left / 30) * 100}%` }} />
      </div>
      <p className="text-sm text-zinc-400">{code} · refreshes every 30s</p>
    </main>
  );
}
```

- [ ] Build green. Commit `feat(p2): kiosk QR display page`.

---

### Task 7: Frontend — scan page + /me

**Files:** Create `frontend/src/app/scan/page.tsx`, `frontend/src/app/me/page.tsx`; Modify `frontend/package.json` (add `jsqr`).

- [ ] `npm i jsqr`
- [ ] `/scan`: getUserMedia rear camera → try `new BarcodeDetector({formats:["qr_code"]})`, else jsQR on canvas frames (10 fps). On decode: parse JSON `{payload, sig}` → `api("/attendance/scan", {method:"POST", body})` → full-screen result state: green "Present ✓ <session>" or red error text with "Try again" button. Guard non-teacher → /login.
- [ ] `/me`: `api("/me")` + `api("/attendance/me")` → profile card (name, employee_id, faculty/department) + stats (present_days / total_sessions) + history table (date, status, method, time). Link from home.
- [ ] Manual browser smoke (documented in working.md): kiosk on one tab, scan with laptop camera OR paste-payload debug input (add a small "paste code" fallback textarea under the camera for devices without camera permission — ponytail, also useful for testing).
- [ ] `npm run build` green. Commit `feat(p2): scanner + my-attendance pages`.

---

### Task 8: Compose smoke + close-out
- [ ] `docker compose up --build -d`; smoke: create kiosk via /docs → login kiosk in browser → /kiosk shows QR; teacher (create via /docs) → /scan (paste-code fallback ok) → Present ✓; second scan → already recorded.
- [ ] Full pytest suite green. Update phases.md (P2 COMPLETED), working.md, DECISIONS.md (cuts: polling not websocket, paste-code fallback, no token purge). Commit `docs: phase 2 complete`, push.

## Done criteria
Suite green; kiosk rotates signed QR every 30s; replay/expired/tampered rejected; one Present per day enforced with exact copy "Attendance already recorded for today."; teacher sees history; all flows audited.
