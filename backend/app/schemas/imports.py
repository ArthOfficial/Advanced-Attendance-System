from typing import Literal

from pydantic import BaseModel


class ImportCounts(BaseModel):
    valid: int
    duplicates: int
    rejected: int


class DuplicateEntry(BaseModel):
    row: dict
    existing: dict


class RejectedEntry(BaseModel):
    row: dict
    reason: str


class ImportPreviewOut(BaseModel):
    import_id: str
    valid: list[dict]
    duplicates: list[DuplicateEntry]
    rejected: list[RejectedEntry]
    counts: ImportCounts


class ImportCommitIn(BaseModel):
    import_id: str
    duplicate_action: Literal["skip", "override"]


class ImportCommitOut(BaseModel):
    created: int
    updated: int
    skipped: int
    rejected: int
