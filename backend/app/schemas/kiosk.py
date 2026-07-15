import uuid

from pydantic import BaseModel, ConfigDict


class KioskCreate(BaseModel):
    name: str
    location: str | None = None


class KioskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    location: str | None
    is_active: bool


class KioskCreated(KioskOut):
    username: str
    password: str


class KioskPatch(BaseModel):
    is_active: bool
