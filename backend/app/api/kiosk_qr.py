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
