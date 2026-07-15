from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.providers.attendance import AttendanceProvider, register_provider
from app.core.qr import verify_payload
from app.models.attendance import Attendance, AttendanceMethod, AttendanceStatus, QRToken


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
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ScanError("already_marked")
        db.refresh(att)
        return att


register_provider(QRProvider())
