"""Attendance schemas per contracts/attendance.md."""

import datetime
import uuid

from pydantic import BaseModel


class AttendanceCreate(BaseModel):
    student_id: uuid.UUID
    batch_id: uuid.UUID
    date: datetime.date
    status: str  # present, absent, late, excused


class AttendanceRecord(BaseModel):
    student_id: uuid.UUID
    status: str


class BulkAttendanceRequest(BaseModel):
    batch_id: uuid.UUID
    date: datetime.date
    records: list[AttendanceRecord]


class AttendanceResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    batch_id: uuid.UUID
    date: datetime.date
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class BulkAttendanceResponse(BaseModel):
    batch_id: uuid.UUID
    date: datetime.date
    marked: int
    errors: list[str] = []


class AttendanceStudentReport(BaseModel):
    student_id: uuid.UUID
    name: str
    present: int
    absent: int
    late: int
    percentage: float
    alert_level: str | None = None


class AttendanceReportResponse(BaseModel):
    batch_id: uuid.UUID
    batch_name: str
    period: dict
    summary: dict
    students: list[AttendanceStudentReport] = []
