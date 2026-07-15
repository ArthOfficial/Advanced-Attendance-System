from datetime import date, datetime

from pydantic import BaseModel


class ScanIn(BaseModel):
    payload: dict
    sig: str


class ScanOut(BaseModel):
    status: str
    session_code: str
    marked_at: datetime


class AttendanceRecord(BaseModel):
    date: date
    status: str
    method: str
    marked_at: datetime | None


class MyAttendanceOut(BaseModel):
    records: list[AttendanceRecord]
    present_days: int
    total_sessions: int
