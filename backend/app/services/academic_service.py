import uuid

from app.models.academic import Department, Faculty, Teacher
from app.repositories.academic_repo import DepartmentRepository, FacultyRepository
from app.services.base import BaseService


class AcademicService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.faculties = FacultyRepository(db)
        self.departments = DepartmentRepository(db)

    # --- faculties ---
    def create_faculty(self, name: str) -> Faculty:
        if self.faculties.get_by_name_ci(name):
            raise ValueError("duplicate")
        return self.faculties.create(name=name)

    def update_faculty(self, id_: uuid.UUID, name: str) -> Faculty:
        fac = self.faculties.get(id_)
        if not fac:
            raise ValueError("not_found")
        existing = self.faculties.get_by_name_ci(name)
        if existing and existing.id != id_:
            raise ValueError("duplicate")
        fac.name = name
        self.db.commit()
        return fac

    def faculty_children(self, id_: uuid.UUID) -> dict:
        if not self.faculties.get(id_):
            raise ValueError("not_found")
        deps = self.departments.list_by_faculty(id_)
        teachers = self.db.query(Teacher).filter_by(faculty_id=id_).all()
        return {"departments": [{"id": str(d.id), "name": d.name} for d in deps],
                "teachers": [{"id": str(t.id), "employee_id": t.employee_id,
                              "full_name": t.full_name} for t in teachers]}

    def delete_faculty(self, id_: uuid.UUID, force: bool = False) -> None:
        fac = self.faculties.get(id_)
        if not fac:
            raise ValueError("not_found")
        deps = self.departments.list_by_faculty(id_)
        if deps and not force:
            raise ValueError("has_children")
        from app.services.teacher_service import delete_teacher_cascade
        for t in self.db.query(Teacher).filter_by(faculty_id=id_).all():
            delete_teacher_cascade(self.db, t)
        self.db.flush()  # teachers must hit the DB before their departments go
        for d in deps:
            self.db.delete(d)
        self.db.delete(fac)
        self.db.commit()

    # --- departments ---
    def create_department(self, name: str, faculty_id: uuid.UUID) -> Department:
        if not self.faculties.get(faculty_id):
            raise ValueError("not_found")
        if self.departments.get_by_name_ci(faculty_id, name):
            raise ValueError("duplicate")
        return self.departments.create(name=name, faculty_id=faculty_id)

    def update_department(self, id_: uuid.UUID, name: str) -> Department:
        dep = self.departments.get(id_)
        if not dep:
            raise ValueError("not_found")
        existing = self.departments.get_by_name_ci(dep.faculty_id, name)
        if existing and existing.id != id_:
            raise ValueError("duplicate")
        dep.name = name
        self.db.commit()
        return dep

    def department_children(self, id_: uuid.UUID) -> dict:
        dep = self.departments.get(id_)
        if not dep:
            raise ValueError("not_found")
        fac = self.faculties.get(dep.faculty_id)
        teachers = self.db.query(Teacher).filter_by(department_id=id_).all()
        return {"faculty": {"id": str(fac.id), "name": fac.name} if fac else None,
                "teachers": [{"id": str(t.id), "employee_id": t.employee_id,
                              "full_name": t.full_name} for t in teachers]}

    def delete_department(self, id_: uuid.UUID, force: bool = False) -> None:
        dep = self.departments.get(id_)
        if not dep:
            raise ValueError("not_found")
        teachers = self.db.query(Teacher).filter_by(department_id=id_).all()
        if teachers and not force:
            raise ValueError("has_children")
        from app.services.teacher_service import delete_teacher_cascade
        for t in teachers:
            delete_teacher_cascade(self.db, t)
        self.db.delete(dep)
        self.db.commit()
