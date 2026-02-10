"""Enrollment schemas per contracts/enrollments.md."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    batch_id: uuid.UUID


class EnrollmentUpdate(BaseModel):
    status: str | None = None


class EnrollmentResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    batch_id: uuid.UUID
    enrollment_date: date
    status: str
    student_name: str | None = None
    batch_name: str | None = None
    course_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
