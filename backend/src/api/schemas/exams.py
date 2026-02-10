"""Exam schemas per contracts/exams.md."""

import datetime
import uuid

from pydantic import BaseModel


class ExamCreate(BaseModel):
    batch_id: uuid.UUID
    title: str
    exam_type: str  # quiz, midterm, final, practical
    date: datetime.date
    total_marks: int


class ExamUpdate(BaseModel):
    title: str | None = None
    exam_type: str | None = None
    date: datetime.date | None = None
    total_marks: int | None = None


class ExamResponse(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    title: str
    exam_type: str
    date: datetime.date
    total_marks: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ExamResultSubmitItem(BaseModel):
    student_id: uuid.UUID
    marks_obtained: float
    grade: str | None = None
    remarks: str | None = None


class ExamResultSubmitRequest(BaseModel):
    results: list[ExamResultSubmitItem]


class ExamResultSubmitResponse(BaseModel):
    exam_id: uuid.UUID
    submitted: int
    errors: list[str] = []


class ExamResultItem(BaseModel):
    student_id: uuid.UUID
    student_name: str
    marks_obtained: float
    percentage: float
    grade: str | None = None
    remarks: str | None = None


class ExamResultStats(BaseModel):
    average: float
    highest: float
    lowest: float
    pass_rate: float


class ExamResultsResponse(BaseModel):
    exam_id: uuid.UUID
    exam_title: str
    total_marks: int
    results: list[ExamResultItem] = []
    stats: ExamResultStats | None = None
