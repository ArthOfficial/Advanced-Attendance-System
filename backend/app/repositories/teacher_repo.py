import uuid

from sqlalchemy.orm import Session

from app.models.academic import Teacher
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, db: Session):
        super().__init__(Teacher, db)

    def get_by_employee_id(self, employee_id: str) -> Teacher | None:
        return self.get_by(employee_id=employee_id)

    def get_by_user_id(self, user_id: uuid.UUID) -> Teacher | None:
        return self.get_by(user_id=user_id)
