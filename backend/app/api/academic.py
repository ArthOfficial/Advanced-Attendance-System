import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_role
from app.core.audit import audit
from app.database import get_db
from app.models.user import User
from app.schemas.academic import (
    DepartmentIn,
    DepartmentOut,
    DepartmentUpdate,
    FacultyIn,
    FacultyOut,
)
from app.services.academic_service import AcademicService

router = APIRouter(tags=["academic"])

_HTTP = {"duplicate": 409, "not_found": 404, "has_children": 409}


def _raise(e: ValueError):
    raise HTTPException(_HTTP.get(str(e), 400), str(e))


@router.post("/faculties", response_model=FacultyOut, status_code=201)
def create_faculty(body: FacultyIn, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        fac = AcademicService(db).create_faculty(body.name)
    except ValueError as e:
        _raise(e)
    audit(db, user.id, "faculty.created", entity=str(fac.id), detail={"name": fac.name})
    return fac


@router.get("/faculties", response_model=list[FacultyOut])
def list_faculties(user: User = Depends(require_role("admin")), db=Depends(get_db)):
    return AcademicService(db).faculties.list()


@router.patch("/faculties/{fid}", response_model=FacultyOut)
def update_faculty(fid: uuid.UUID, body: FacultyIn, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        fac = AcademicService(db).update_faculty(fid, body.name)
    except ValueError as e:
        _raise(e)
    audit(db, user.id, "faculty.updated", entity=str(fid), detail={"name": body.name})
    return fac


@router.delete("/faculties/{fid}", status_code=204)
def delete_faculty(fid: uuid.UUID, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        AcademicService(db).delete_faculty(fid)
    except ValueError as e:
        _raise(e)
    audit(db, user.id, "faculty.deleted", entity=str(fid))


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(body: DepartmentIn, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        dep = AcademicService(db).create_department(body.name, body.faculty_id)
    except ValueError as e:
        _raise(e)
    audit(db, user.id, "department.created", entity=str(dep.id), detail={"name": dep.name})
    return dep


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(faculty_id: uuid.UUID | None = None, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    svc = AcademicService(db)
    if faculty_id:
        return svc.departments.list_by_faculty(faculty_id)
    return svc.departments.list()


@router.patch("/departments/{did}", response_model=DepartmentOut)
def update_department(did: uuid.UUID, body: DepartmentUpdate, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        dep = AcademicService(db).update_department(did, body.name)
    except ValueError as e:
        _raise(e)
    audit(db, user.id, "department.updated", entity=str(did), detail={"name": body.name})
    return dep


@router.delete("/departments/{did}", status_code=204)
def delete_department(did: uuid.UUID, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        AcademicService(db).delete_department(did)
    except ValueError as e:
        _raise(e)
    audit(db, user.id, "department.deleted", entity=str(did))
