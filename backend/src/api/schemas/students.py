"""Student schemas per contracts/students.md."""

import datetime
import uuid

from pydantic import BaseModel, EmailStr


class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    cnic: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    address: str | None = None


class StudentUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    cnic: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    address: str | None = None
    status: str | None = None


class StudentResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str
    cnic: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    address: str | None = None
    enrollment_date: datetime.date
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class AttendanceRecord(BaseModel):
    date: datetime.date
    status: str


class StudentAttendanceSummary(BaseModel):
    student_id: uuid.UUID
    total_classes: int
    present: int
    absent: int
    late: int
    percentage: float
    alert_level: str | None = None
    records: list[AttendanceRecord] = []


class StudentFeeItem(BaseModel):
    id: uuid.UUID
    course_name: str
    amount: float
    paid_amount: float
    due_date: datetime.date
    status: str
    alert_level: str | None = None


class StudentFeesSummary(BaseModel):
    student_id: uuid.UUID
    fees: list[StudentFeeItem] = []
    total_due: float
    total_paid: float
