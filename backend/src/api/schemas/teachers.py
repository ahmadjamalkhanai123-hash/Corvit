"""Teacher schemas per contracts/teachers.md."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    specialization: str | None = None
    qualification: str | None = None


class TeacherUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    specialization: str | None = None
    qualification: str | None = None
    is_active: bool | None = None


class TeacherResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str
    specialization: str | None = None
    qualification: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TeacherBatchItem(BaseModel):
    id: uuid.UUID
    name: str
    course_name: str
    schedule_days: str | None = None
    schedule_time: str | None = None
    student_count: int
    status: str


class TeacherBatchesResponse(BaseModel):
    teacher_id: uuid.UUID
    batches: list[TeacherBatchItem] = []
