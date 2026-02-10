"""Fee schemas per contracts/fees.md."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class FeeCreate(BaseModel):
    student_id: uuid.UUID
    course_id: uuid.UUID
    amount: float
    due_date: date


class FeeUpdate(BaseModel):
    amount: float | None = None
    due_date: date | None = None
    status: str | None = None


class FeePayRequest(BaseModel):
    amount: float
    payment_date: date | None = None


class FeeResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    amount: float
    paid_amount: float
    due_date: date
    paid_date: date | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeePaymentResponse(BaseModel):
    id: uuid.UUID
    amount: float
    paid_amount: float
    remaining: float
    status: str
    paid_date: date | None = None


class OverdueFeeItem(BaseModel):
    id: uuid.UUID
    student_name: str
    course_name: str
    amount: float
    paid_amount: float
    due_date: date
    days_overdue: int
    alert_level: str
    status: str


class OverdueFeeResponse(BaseModel):
    items: list[OverdueFeeItem] = []
    total_overdue_count: int
    total_overdue_amount: float
