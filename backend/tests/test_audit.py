from app.core.audit import audit
from app.database import SessionLocal
from app.models.infra import AuditLog


def test_audit_writes_row():
    db = SessionLocal()
    try:
        before = db.query(AuditLog).count()
        audit(db, None, "test.event", entity="thing", detail={"k": "v"})
        assert db.query(AuditLog).count() == before + 1
        row = db.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
        assert row.action == "test.event" and row.detail == {"k": "v"}
    finally:
        db.close()
