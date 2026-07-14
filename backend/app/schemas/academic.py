import uuid

from pydantic import BaseModel, ConfigDict


class FacultyIn(BaseModel):
    name: str


class FacultyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class DepartmentIn(BaseModel):
    name: str
    faculty_id: uuid.UUID


class DepartmentUpdate(BaseModel):
    name: str


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    faculty_id: uuid.UUID
