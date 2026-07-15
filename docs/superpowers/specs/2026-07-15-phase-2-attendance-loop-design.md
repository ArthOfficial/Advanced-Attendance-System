# Phase 2 — Core Attendance Loop — Design Spec

Date: 2026-07-15 · Status: Approved · Part of V1 (see phases.md)

## Goal
Kiosk displays a 30s-rotating signed QR; teacher scans it in the PWA; server validates and
marks Present once per daily session. First real UI (login, kiosk, scan, me).

## Backend

### Daily sessions — SessionService
- `get_or_create_today() -> AttendanceSession`: active session for server date, else create
  `ATT-YYYY-MM-DD` (session_date unique ⇒ concurrent create falls back to select). Deactivates
  older active sessions. Recovery order (spec): server date → last session date → last QR issued_at
  (only matters if server date is obviously wrong, i.e. before last known activity — then reuse last session).

### Kiosk management (admin)
- `POST /kiosks {name, location}` → kiosk users row (username `kiosk-<slug>` as email field,
  auto password via `secrets.token_urlsafe(8)`) + attendance_kiosks row. Password returned ONCE.
- `GET /kiosks`, `PATCH /kiosks/{id}` (is_active). Kiosk logs in via existing /auth/login.

### QR issue (kiosk role)
- `GET /kiosk/qr` → qr_tokens row (token=token_urlsafe(32), nonce=token_urlsafe(8),
  issued_at, expires_at=+30s, session_id, kiosk_id) → returns
  `{payload: {sid, tok, iat, exp, nonce}, sig: HMAC-SHA256(jwt_secret, canonical-json), session_code}`.
- Kiosk page polls every 30s. Old tokens die by expiry; no cleanup job in V1
  (ponytail: rows are tiny; add a purge in P5 if the table ever matters).

### Scan (teacher role) — QRProvider(AttendanceProvider), registered in PROVIDERS
- `POST /attendance/scan {payload, sig}` → verify HMAC → token row exists, unused, unexpired,
  session is today's active → in ONE transaction: set used_at + insert attendance
  (present, QR, device fingerprint optional later, marked_at=now).
- Duplicate (unique teacher+session) → 409 "Attendance already recorded for today."
- Failures audited: attendance.scan.{success,expired,replayed,bad_signature,wrong_session}.

### Teacher history
- `GET /attendance/me` → list of {date, status, marked_at, method} + {present_days, total_sessions}.

## Frontend (Next.js, Tailwind, dark; first real UI)
- Shared: tiny fetch wrapper w/ JWT from localStorage, backend URL from NEXT_PUBLIC_API_URL.
- `/login`: identifier+password → store tokens; force_password_reset → `/change-password`.
- `/change-password`: old+new → POST, then to role home.
- `/kiosk`: fullscreen QR (client-rendered from payload JSON string via `qrcode` npm lib),
  30s auto-refresh + countdown, session code footer. Kiosk account only.
- `/scan`: camera (native BarcodeDetector; jsQR fallback), decode → POST scan →
  fullscreen green "Present ✓" or red error. Teacher only.
- `/me`: profile + history table.

## Tests (backend; UI manually smoke-tested in browser)
Session idempotency; scan happy path; replay rejected; expired rejected (freeze via monkeypatched
now); wrong-session rejected; duplicate → 409 message; RBAC: teacher can't GET /kiosk/qr,
kiosk can't POST /attendance/scan; kiosk create returns one-time password that can log in.

## Cut corners (DECISIONS.md)
No websocket push (poll 30s). No device fingerprinting yet (devices table unused until P4).
No token purge job. QR payload is plain JSON string in the QR image.
