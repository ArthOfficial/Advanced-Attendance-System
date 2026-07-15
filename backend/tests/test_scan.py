import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core import security
from app.core.qr import verify_payload
from app.database import SessionLocal
from app.main import app
from app.models.academic import Department, Faculty, Teacher
from app.models.attendance import QRToken
from app.models.user import Role, User
from app.services.session_service import SessionService

client = TestClient(app)


def _headers(role: Role):
    db = SessionLocal()
    u = User(email=f"{role.value}-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=role)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role=role.value)}"}


def _teacher_headers():
    db = SessionLocal()
    fac = Faculty(name=f"F-{uuid.uuid4().hex[:6]}"); db.add(fac); db.flush()
    dep = Department(name="D", faculty_id=fac.id); db.add(dep); db.flush()
    u = User(email=None, password_hash=security.hash_password("pw"), role=Role.teacher)
    db.add(u); db.flush()
    t = Teacher(user_id=u.id, faculty_id=fac.id, department_id=dep.id,
                employee_id=f"EMP{uuid.uuid4().hex[:8]}", full_name="T", dob=date(1990, 1, 1))
    db.add(t); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='teacher')}"}


def _qr():
    return client.get("/kiosk/qr", headers=_headers(Role.kiosk)).json()


def test_session_idempotent():
    db = SessionLocal()
    try:
        s1 = SessionService(db).get_or_create_today()
        s2 = SessionService(db).get_or_create_today()
        assert s1.id == s2.id and s1.is_active
        assert s1.session_code == f"ATT-{s1.session_date.isoformat()}"
    finally:
        db.close()


def test_qr_issue_signed_and_rbac():
    r = client.get("/kiosk/qr", headers=_headers(Role.kiosk))
    assert r.status_code == 200
    b = r.json()
    assert verify_payload(b["payload"], b["sig"])
    assert b["payload"]["exp"] - b["payload"]["iat"] == 30
    assert client.get("/kiosk/qr", headers=_teacher_headers()).status_code == 403


def test_kiosk_create_password_logs_in():
    h = _headers(Role.admin)
    r = client.post("/kiosks", json={"name": "Gate A", "location": "Main"}, headers=h)
    assert r.status_code == 201
    b = r.json()
    assert client.post("/auth/login", json={"identifier": b["username"],
                                            "password": b["password"]}).status_code == 200
    client.patch(f"/kiosks/{b['id']}", json={"is_active": False}, headers=h)
    assert client.post("/auth/login", json={"identifier": b["username"],
                                            "password": b["password"]}).status_code == 401


def test_scan_happy_duplicate_replay():
    th = _teacher_headers()
    qr = _qr()
    r = client.post("/attendance/scan", json={"payload": qr["payload"], "sig": qr["sig"]}, headers=th)
    assert r.status_code == 200 and r.json()["status"] == "present"
    qr2 = _qr()
    r2 = client.post("/attendance/scan", json={"payload": qr2["payload"], "sig": qr2["sig"]}, headers=th)
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Attendance already recorded for today."
    r3 = client.post("/attendance/scan", json={"payload": qr["payload"], "sig": qr["sig"]},
                     headers=_teacher_headers())
    assert r3.status_code == 400 and "already used" in r3.json()["detail"]


def test_scan_tampered_expired_rbac_history():
    th = _teacher_headers()
    qr = _qr()
    bad = dict(qr["payload"]); bad["tok"] = "forged"
    assert client.post("/attendance/scan", json={"payload": bad, "sig": qr["sig"]},
                       headers=th).status_code == 400
    qr2 = _qr()
    db = SessionLocal()
    tok = db.query(QRToken).filter_by(token=qr2["payload"]["tok"]).one()
    tok.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit(); db.close()
    r = client.post("/attendance/scan", json={"payload": qr2["payload"], "sig": qr2["sig"]}, headers=th)
    assert r.status_code == 400 and "expired" in r.json()["detail"]
    # kiosk can't scan
    qr3 = _qr()
    assert client.post("/attendance/scan", json={"payload": qr3["payload"], "sig": qr3["sig"]},
                       headers=_headers(Role.kiosk)).status_code == 403
    # history
    client.post("/attendance/scan", json={"payload": qr3["payload"], "sig": qr3["sig"]}, headers=th)
    me = client.get("/attendance/me", headers=th)
    assert me.status_code == 200 and me.json()["present_days"] == 1
