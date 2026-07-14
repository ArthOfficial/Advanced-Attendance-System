import uuid

from app.core.passwords import dob_password
from app.core.security import hash_password
from app.models.academic import Teacher
from app.models.user import Role, User
from app.repositories.academic_repo import DepartmentRepository, FacultyRepository
from app.repositories.teacher_repo import TeacherRepository
from app.schemas.teacher import TeacherCreate
from app.services.base import BaseService


class TeacherService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.teachers = TeacherRepository(db)
        self.faculties = FacultyRepository(db)
        self.departments = DepartmentRepository(db)

    def create_teacher(self, data: TeacherCreate) -> Teacher:
        if self.teachers.get_by_employee_id(data.employee_id):
            raise ValueError("duplicate")
        fac = self.faculties.get(data.faculty_id)
        dep = self.departments.get(data.department_id)
        if not fac or not dep:
            raise ValueError("not_found")
        if dep.faculty_id != fac.id:
            raise ValueError("mismatch")
        user = User(
            email=data.email,
            password_hash=hash_password(dob_password(data.dob)),
            role=Role.teacher,
            force_password_reset=True,
        )
        self.db.add(user)
        self.db.flush()  # single transaction: user + teacher commit together
        teacher = Teacher(
            user_id=user.id, faculty_id=data.faculty_id, department_id=data.department_id,
            employee_id=data.employee_id, full_name=data.full_name, dob=data.dob,
            designation=data.designation, email=data.email,
        )
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def list_teachers(self, faculty_id: uuid.UUID | None = None,
                      department_id: uuid.UUID | None = None, q: str | None = None) -> list[Teacher]:
        query = self.db.query(Teacher)
        if faculty_id:
            query = query.filter_by(faculty_id=faculty_id)
        if department_id:
            query = query.filter_by(department_id=department_id)
        if q:
            like = f"%{q}%"
            query = query.filter(Teacher.full_name.ilike(like) | Teacher.employee_id.ilike(like))
        return query.all()
