import uuid
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.database import Base

M = TypeVar("M", bound=Base)


class BaseRepository(Generic[M]):
    def __init__(self, model: type[M], db: Session):
        self.model = model
        self.db = db

    def get(self, id_: uuid.UUID) -> M | None:
        return self.db.get(self.model, id_)

    def get_by(self, **kw) -> M | None:
        return self.db.query(self.model).filter_by(**kw).first()

    def list(self) -> list[M]:
        return self.db.query(self.model).all()

    def create(self, **kw) -> M:
        obj = self.model(**kw)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
