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

    def delete_faculty(self, id_: uuid.UUID) -> None:
        fac = self.faculties.get(id_)
        if not fac:
            raise ValueError("not_found")
        if self.departments.list_by_faculty(id_):
            raise ValueError("has_children")
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

    def delete_department(self, id_: uuid.UUID) -> None:
        dep = self.departments.get(id_)
        if not dep:
            raise ValueError("not_found")
        has_teachers = self.db.query(Teacher).filter_by(department_id=id_).first()
        if has_teachers:
            raise ValueError("has_children")
        self.db.delete(dep)
        self.db.commit()
