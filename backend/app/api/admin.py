import ipaddress
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import require_role
from app.core.audit import audit
from app.database import get_db
from app.models.academic import Teacher
from app.models.attendance import Attendance, AttendanceSession, AttendanceStatus
from app.models.infra import AttendanceKiosk, AuditLog, SystemSetting
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping(user: User = Depends(require_role("admin"))):
    return {"pong": True}


@router.get("/stats")
def stats(day: date | None = None, faculty_id: uuid.UUID | None = None,
          department_id: uuid.UUID | None = None,
          user: User = Depends(require_role("admin")), db=Depends(get_db)):
    tq = db.query(Teacher)
    if faculty_id:
        tq = tq.filter_by(faculty_id=faculty_id)
    if department_id:
        tq = tq.filter_by(department_id=department_id)
    total = tq.count()
    session = None
    if day:
        session = db.query(AttendanceSession).filter_by(session_date=day).first()
    else:
        session = (db.query(AttendanceSession).filter_by(is_active=True)
                   .order_by(AttendanceSession.session_date.desc()).first())
    present = 0
    if session:
        aq = (db.query(Attendance).join(Teacher, Attendance.teacher_id == Teacher.id)
              .filter(Attendance.session_id == session.id,
                      Attendance.status == AttendanceStatus.present))
        if faculty_id:
            aq = aq.filter(Teacher.faculty_id == faculty_id)
        if department_id:
            aq = aq.filter(Teacher.department_id == department_id)
        present = aq.count()
    kiosks = db.query(AttendanceKiosk).filter_by(is_active=True).count()
    return {
        "total_teachers": total, "present": present, "absent": max(0, total - present),
        "percent": round(present * 100 / total, 1) if total else 0.0,
        "session_code": session.session_code if session else None,
        "session_date": session.session_date.isoformat() if session else None,
        "active_kiosks": kiosks,
    }


@router.get("/audit")
def audit_log(q: str | None = None, action: str | None = None,
              limit: int = Query(50, le=200), offset: int = 0,
              user: User = Depends(require_role("admin")), db=Depends(get_db)):
    qry = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        qry = qry.filter(AuditLog.action.ilike(f"%{action}%"))
    if q:
        qry = qry.filter(AuditLog.detail.cast(sa_text_type()).ilike(f"%{q}%"))
    rows = qry.offset(offset).limit(limit).all()
    return [{"id": str(r.id), "action": r.action, "entity": r.entity, "detail": r.detail,
             "ip": r.ip, "actor": str(r.actor_user_id) if r.actor_user_id else None,
             "at": r.created_at.isoformat()} for r in rows]


def sa_text_type():
    from sqlalchemy import String
    return String


NETWORK_KEY = "allowed_networks"  # {"enabled": bool, "cidrs": ["192.168.0.0/16", ...]}


def get_network_setting(db) -> dict:
    row = db.query(SystemSetting).filter_by(key=NETWORK_KEY).first()
    return row.value if row and row.value else {"enabled": False, "cidrs": []}


def client_ip_allowed(request: Request, db) -> bool:
    cfg = get_network_setting(db)
    if not cfg.get("enabled"):
        return True
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "").split(",")[0].strip()
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        # ponytail: unparseable host (test client, odd proxy) → fail-open; real LAN clients always have an IP
        return True
    if addr.is_loopback:  # local testing
        return True
    return any(addr in ipaddress.ip_network(c, strict=False) for c in cfg.get("cidrs", []))


@router.get("/settings/network")
def get_network(user: User = Depends(require_role("admin")), db=Depends(get_db)):
    return get_network_setting(db)


@router.put("/settings/network")
def put_network(body: dict, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    for c in body.get("cidrs", []):
        try:
            ipaddress.ip_network(c, strict=False)
        except ValueError:
            raise HTTPException(422, f"invalid CIDR: {c}")
    row = db.query(SystemSetting).filter_by(key=NETWORK_KEY).first()
    if row:
        row.value = {"enabled": bool(body.get("enabled")), "cidrs": body.get("cidrs", [])}
    else:
        row = SystemSetting(key=NETWORK_KEY,
                            value={"enabled": bool(body.get("enabled")), "cidrs": body.get("cidrs", [])})
        db.add(row)
    db.commit()
    audit(db, user.id, "settings.network.updated", detail=row.value)
    return row.value
