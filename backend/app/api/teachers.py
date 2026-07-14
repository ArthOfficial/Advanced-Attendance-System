import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_role
from app.core.audit import audit
from app.database import get_db
from app.models.user import User
from app.schemas.teacher import TeacherCreate, TeacherMe, TeacherOut
from app.services.teacher_service import TeacherService

router = APIRouter(tags=["teachers"])

_HTTP = {"duplicate": 409, "not_found": 404, "mismatch": 422}


@router.post("/teachers", response_model=TeacherOut, status_code=201)
def create_teacher(body: TeacherCreate, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    try:
        t = TeacherService(db).create_teacher(body)
    except ValueError as e:
        raise HTTPException(_HTTP.get(str(e), 400), str(e))
    audit(db, user.id, "teacher.created", entity=str(t.id), detail={"employee_id": t.employee_id})
    return t


@router.get("/teachers", response_model=list[TeacherOut])
def list_teachers(faculty_id: uuid.UUID | None = None, department_id: uuid.UUID | None = None,
                  q: str | None = None, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    return TeacherService(db).list_teachers(faculty_id, department_id, q)


@router.get("/teachers/{tid}", response_model=TeacherOut)
def get_teacher(tid: uuid.UUID, user: User = Depends(require_role("admin")), db=Depends(get_db)):
    t = TeacherService(db).teachers.get(tid)
    if not t:
        raise HTTPException(404, "not_found")
    return t


@router.get("/me", response_model=TeacherMe)
def me(user: User = Depends(require_role("teacher")), db=Depends(get_db)):
    svc = TeacherService(db)
    t = svc.teachers.get_by_user_id(user.id)
    if not t:
        raise HTTPException(404, "not_found")
    fac = svc.faculties.get(t.faculty_id)
    dep = svc.departments.get(t.department_id)
    return TeacherMe(
        id=t.id, employee_id=t.employee_id, full_name=t.full_name, dob=t.dob,
        faculty_id=t.faculty_id, department_id=t.department_id,
        designation=t.designation, email=t.email,
        faculty_name=fac.name, department_name=dep.name,
        force_password_reset=user.force_password_reset,
    )
