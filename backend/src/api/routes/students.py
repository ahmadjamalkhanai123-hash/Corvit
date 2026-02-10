"""Student routes per contracts/students.md."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.students import (
    AttendanceRecord,
    StudentAttendanceSummary,
    StudentCreate,
    StudentFeeItem,
    StudentFeesSummary,
    StudentResponse,
    StudentUpdate,
)
from src.auth.dependencies import get_current_user, require_role
from src.database.models import (
    Attendance,
    AttendanceStatus,
    Course,
    Enrollment,
    EnrollmentStatus,
    Fee,
    Student,
    StudentStatus,
    User,
)
from src.rules.engine import RuleEngine

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    body: StudentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    existing = await db.execute(select(Student).where(Student.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    student = Student(**body.model_dump())
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("", response_model=PaginatedResponse)
async def list_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    sort_by: str = "name",
    sort_order: str = "asc",
):
    query = select(Student)
    count_query = select(func.count()).select_from(Student)

    if search:
        query = query.where(Student.name.ilike(f"%{search}%"))
        count_query = count_query.where(Student.name.ilike(f"%{search}%"))
    if status_filter:
        query = query.where(Student.status == StudentStatus(status_filter))
        count_query = count_query.where(Student.status == StudentStatus(status_filter))

    sort_col = getattr(Student, sort_by, Student.name)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    students = result.scalars().all()

    return PaginatedResponse(
        items=[StudentResponse.model_validate(s) for s in students],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = StudentStatus(update_data["status"])
    for key, value in update_data.items():
        setattr(student, key, value)

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Check active enrollments
    active_enrollments = await db.execute(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.status == EnrollmentStatus.active,
        )
    )
    if (active_enrollments.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete student with active enrollments",
        )

    await db.delete(student)
    await db.commit()


@router.get("/{student_id}/attendance", response_model=StudentAttendanceSummary)
async def get_student_attendance(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    batch_id: uuid.UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
):
    # Build query
    query = select(Attendance).where(Attendance.student_id == student_id)
    if batch_id:
        query = query.where(Attendance.batch_id == batch_id)
    if from_date:
        query = query.where(Attendance.date >= from_date)
    if to_date:
        query = query.where(Attendance.date <= to_date)

    query = query.order_by(Attendance.date.desc())
    result = await db.execute(query)
    records = result.scalars().all()

    total = len(records)
    present = sum(1 for r in records if r.status in (AttendanceStatus.present, AttendanceStatus.late))
    absent = sum(1 for r in records if r.status == AttendanceStatus.absent)
    late = sum(1 for r in records if r.status == AttendanceStatus.late)
    percentage = (present / total * 100) if total > 0 else 0.0

    alert_level = None
    if total > 0:
        engine = RuleEngine()
        alert = engine.evaluate_attendance_percentage(percentage)
        alert_level = alert.level if alert.level != "none" else None

    return StudentAttendanceSummary(
        student_id=student_id,
        total_classes=total,
        present=present - late,  # present excludes late
        absent=absent,
        late=late,
        percentage=round(percentage, 1),
        alert_level=alert_level,
        records=[AttendanceRecord(date=r.date, status=r.status.value) for r in records],
    )


@router.get("/{student_id}/fees", response_model=StudentFeesSummary)
async def get_student_fees(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Fee).where(Fee.student_id == student_id).options(selectinload(Fee.course))
    )
    fees = result.scalars().all()

    engine = RuleEngine()
    today = date.today()
    fee_items = []
    total_due = 0.0
    total_paid = 0.0

    for fee in fees:
        days_overdue = (today - fee.due_date).days
        alert_level = None
        if days_overdue > 0 and fee.status.value != "paid":
            alert = engine.evaluate_fee_overdue(days_overdue)
            alert_level = alert.level if alert.level != "none" else None

        remaining = float(fee.amount - fee.paid_amount)
        total_due += remaining if remaining > 0 else 0
        total_paid += float(fee.paid_amount)

        fee_items.append(StudentFeeItem(
            id=fee.id,
            course_name=fee.course.name if fee.course else "Unknown",
            amount=float(fee.amount),
            paid_amount=float(fee.paid_amount),
            due_date=fee.due_date,
            status=fee.status.value,
            alert_level=alert_level,
        ))

    return StudentFeesSummary(
        student_id=student_id,
        fees=fee_items,
        total_due=total_due,
        total_paid=total_paid,
    )
