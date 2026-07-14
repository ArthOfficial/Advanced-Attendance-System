import uuid

from sqlalchemy.orm import Session

from app.models.infra import AuditLog


def audit(db: Session, actor_id: uuid.UUID | None, action: str,
          entity: str | None = None, detail: dict | None = None, ip: str | None = None) -> None:
    db.add(AuditLog(actor_user_id=actor_id, action=action, entity=entity, detail=detail, ip=ip))
    db.commit()
