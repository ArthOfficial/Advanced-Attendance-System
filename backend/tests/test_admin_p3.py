import uuid

from fastapi.testclient import TestClient

from app.core import security
from app.database import SessionLocal
from app.main import app
from app.models.user import Role, User

client = TestClient(app)


def _admin():
    db = SessionLocal()
    u = User(email=f"a-{uuid.uuid4().hex[:6]}@x.local",
             password_hash=security.hash_password("pw"), role=Role.admin)
    db.add(u); db.commit(); db.refresh(u); db.close()
    return {"Authorization": f"Bearer {security.create_access_token(sub=str(u.id), role='admin')}"}


def test_stats_and_audit():
    h = _admin()
    s = client.get("/admin/stats", headers=h)
    assert s.status_code == 200 and "total_teachers" in s.json()
    a = client.get("/admin/audit", params={"action": "login"}, headers=h)
    assert a.status_code == 200 and isinstance(a.json(), list)


def test_reports_json_and_csv():
    h = _admin()
    r = client.get("/admin/reports", params={
        "date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "faculty"}, headers=h)
    assert r.status_code == 200
    b = r.json()
    assert "rows" in b and b["group_by"] == "faculty"
    c = client.get("/admin/reports", params={
        "date_from": "2026-01-01", "date_to": "2026-12-31", "fmt": "csv"}, headers=h)
    assert c.status_code == 200 and c.headers["content-type"].startswith("text/csv")
    assert client.get("/admin/reports", params={
        "date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "bogus"},
        headers=h).status_code == 422


def test_network_settings_roundtrip_and_loopback_ok():
    h = _admin()
    r = client.put("/admin/settings/network",
                   json={"enabled": True, "cidrs": ["192.168.0.0/16"]}, headers=h)
    assert r.status_code == 200 and r.json()["enabled"] is True
    assert client.put("/admin/settings/network",
                      json={"enabled": True, "cidrs": ["bad"]}, headers=h).status_code == 422
    # loopback (testclient) still allowed even when enabled
    from datetime import date
    db = SessionLocal()
    from app.models.academic import Department, Faculty, Teacher
    fac = Faculty(name=f"F-{uuid.uuid4().hex[:6]}"); db.add(fac); db.flush()
    dep = Department(name="D", faculty_id=fac.id); db.add(dep); db.flush()
    tu = User(email=None, password_hash=security.hash_password("pw"), role=Role.teacher)
    db.add(tu); db.flush()
    db.add(Teacher(user_id=tu.id, faculty_id=fac.id, department_id=dep.id,
                   employee_id=f"EMP{uuid.uuid4().hex[:8]}", full_name="T", dob=date(1990, 1, 1)))
    db.commit(); db.refresh(tu); db.close()
    th = {"Authorization": f"Bearer {security.create_access_token(sub=str(tu.id), role='teacher')}"}
    r2 = client.post("/attendance/scan", json={"payload": {}, "sig": "x"}, headers=th)
    assert r2.status_code == 400  # got past network check → bad signature
    client.put("/admin/settings/network", json={"enabled": False, "cidrs": []}, headers=h)
