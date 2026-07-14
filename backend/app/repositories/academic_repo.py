import uuid

from sqlalchemy.orm import Session

from app.models.academic import Department, Faculty
from app.repositories.base import BaseRepository


class FacultyRepository(BaseRepository[Faculty]):
    def __init__(self, db: Session):
        super().__init__(Faculty, db)

    def get_by_name_ci(self, name: str) -> Faculty | None:
        return self.db.query(Faculty).filter(Faculty.name.ilike(name)).first()


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session):
        super().__init__(Department, db)

    def list_by_faculty(self, faculty_id: uuid.UUID) -> list[Department]:
        return self.db.query(Department).filter_by(faculty_id=faculty_id).all()

    def get_by_name_ci(self, faculty_id: uuid.UUID, name: str) -> Department | None:
        return (self.db.query(Department)
                .filter(Department.faculty_id == faculty_id, Department.name.ilike(name))
                .first())
