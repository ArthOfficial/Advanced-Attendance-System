from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import require_role
from app.core.audit import audit
from app.core.providers.attendance import get_provider
from app.core.providers.qr_provider import ScanError
from app.database import get_db
from app.models.attendance import Attendance, AttendanceSession
from app.models.user import User
from app.repositories.teacher_repo import TeacherRepository
from app.schemas.attendance import AttendanceRecord, MyAttendanceOut, ScanIn, ScanOut

router = APIRouter(prefix="/attendance", tags=["attendance"])

_MSG = {
    "bad_signature": "Invalid QR code.",
    "unknown_token": "Invalid QR code.",
    "expired": "QR code expired. Scan the current code.",
    "replayed": "This QR code was already used.",
    "wrong_session": "QR code is not for today's session.",
}


@router.post("/scan", response_model=ScanOut)
def scan(request: Request, body: ScanIn, user: User = Depends(require_role("teacher")), db=Depends(get_db)):
    from app.api.admin import client_ip_allowed
    if not client_ip_allowed(request, db):
        audit(db, user.id, "attendance.scan.network_blocked")
        raise HTTPException(403, "You must be connected to the University Network.")
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
