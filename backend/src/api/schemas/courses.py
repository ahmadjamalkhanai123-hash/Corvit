"""Course schemas per contracts/courses.md."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CourseCreate(BaseModel):
    name: str
    code: str
    duration_weeks: int
    fee_amount: float
    description: str | None = None
    category: str | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    duration_weeks: int | None = None
    fee_amount: float | None = None
    description: str | None = None
    category: str | None = None
    is_active: bool | None = None


class CourseResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    duration_weeks: int
    fee_amount: float
    description: str | None = None
    category: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseBatchItem(BaseModel):
    id: uuid.UUID
    name: str
    teacher_name: str
    schedule_days: str | None = None
    schedule_time: str | None = None
    start_date: str | None = None
    enrolled: int
    max_capacity: int
    seats_available: int
    status: str


class CourseBatchesResponse(BaseModel):
    course_id: uuid.UUID
    course_name: str
    batches: list[CourseBatchItem] = []
