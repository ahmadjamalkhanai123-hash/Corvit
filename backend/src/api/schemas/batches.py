"""Batch schemas per contracts/batches.md."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class BatchCreate(BaseModel):
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    name: str
    room: str | None = None
    schedule_days: str | None = None
    schedule_time: str | None = None
    start_date: date
    end_date: date | None = None
    max_capacity: int = 30


class BatchUpdate(BaseModel):
    name: str | None = None
    room: str | None = None
    schedule_days: str | None = None
    schedule_time: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    max_capacity: int | None = None
    status: str | None = None


class BatchResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    teacher_id: uuid.UUID
    name: str
    room: str | None = None
    schedule_days: str | None = None
    schedule_time: str | None = None
    start_date: date
    end_date: date | None = None
    max_capacity: int
    status: str
    course_name: str | None = None
    teacher_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchStudentItem(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    enrollment_status: str
    attendance_percentage: float | None = None


class BatchStudentsResponse(BaseModel):
    batch_id: uuid.UUID
    batch_name: str
    students: list[BatchStudentItem] = []
    total_enrolled: int


class BatchScheduleResponse(BaseModel):
    batch_id: uuid.UUID
    batch_name: str
    course_name: str
    teacher_name: str
    room: str | None = None
    schedule_days: str | None = None
    schedule_time: str | None = None
    start_date: date
    end_date: date | None = None
