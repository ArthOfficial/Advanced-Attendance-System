from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping(user: User = Depends(require_role("admin"))):
    return {"pong": True}
