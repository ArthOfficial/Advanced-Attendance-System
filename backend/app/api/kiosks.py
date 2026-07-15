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
    ku.is_active = body.is_active
    db.commit()
    audit(db, user.id, "kiosk.updated", entity=str(kid), detail={"is_active": body.is_active})
    return k
