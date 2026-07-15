from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import require_role
from app.core.audit import audit
from app.database import get_db
from app.models.user import User
from app.schemas.imports import ImportCommitIn, ImportCommitOut, ImportPreviewOut
from app.services.import_service import ImportService

router = APIRouter(prefix="/teachers/import", tags=["import"])

ALLOWED = (".csv", ".xlsx", ".xls")
_HTTP = {"not_found": 404, "expired": 410, "consumed": 410}


@router.post("/preview", response_model=ImportPreviewOut)
async def preview(file: UploadFile, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(ALLOWED):
        raise HTTPException(422, "unsupported file type (use .csv, .xlsx, .xls)")
    content = await file.read()
    return ImportService(db).preview(content, file.filename, user.id)


@router.post("/commit", response_model=ImportCommitOut)
def commit(body: ImportCommitIn, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        result = ImportService(db).commit(body.import_id, body.duplicate_action, user.id)
    except ValueError as e:
        raise HTTPException(_HTTP.get(str(e), 400), str(e))
    audit(db, user.id, "teachers.import.committed",
          detail={**result, "duplicate_action": body.duplicate_action})
    return result
