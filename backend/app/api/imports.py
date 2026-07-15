from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import require_role
from app.database import get_db
from app.models.user import User
from app.schemas.imports import ImportPreviewOut
from app.services.import_service import ImportService

router = APIRouter(prefix="/teachers/import", tags=["import"])

ALLOWED = (".csv", ".xlsx", ".xls")


@router.post("/preview", response_model=ImportPreviewOut)
async def preview(file: UploadFile, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(ALLOWED):
        raise HTTPException(422, "unsupported file type (use .csv, .xlsx, .xls)")
    content = await file.read()
    return ImportService(db).preview(content, file.filename, user.id)
