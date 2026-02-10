"""Attendance routes per contracts/attendance.md."""

import uuid
from datetime import date as date_type
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceReportResponse,
    AttendanceStudentReport,
    BulkAttendanceRequest,
    BulkAttendanceResponse,
)
from src.api.schemas.common import PaginatedResponse
from src.auth.dependencies import get_current_user, require_role
from src.database.models import (
    Attendance,
    AttendanceStatus,
    Batch,
    Enrollment,
    Student,
    User,
)
from src.rules.engine import RuleEngine

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    body: AttendanceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin", "teacher"))],
):
    # Check duplicate
    existing = await db.execute(
        select(Attendance).where(
            Attendance.student_id == body.student_id,
            Attendance.batch_id == body.batch_id,
            Attendance.date == body.date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already marked for this student on this date",
        )

    attendance = Attendance(
        student_id=body.student_id,
        batch_id=body.batch_id,
        date=body.date,
        status=AttendanceStatus(body.status),
        marked_by=current_user.id,
    )
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.get("", response_model=PaginatedResponse)
async def list_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    batch_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    date: date_type | None = None,
    status_filter: str | None = Query(None, alias="status"),
):
    query = select(Attendance)
    count_query = select(func.count()).select_from(Attendance)

    if batch_id:
        query = query.where(Attendance.batch_id == batch_id)
        count_query = count_query.where(Attendance.batch_id == batch_id)
    if student_id:
        query = query.where(Attendance.student_id == student_id)
        count_query = count_query.where(Attendance.student_id == student_id)
    if date:
        query = query.where(Attendance.date == date)
        count_query = count_query.where(Attendance.date == date)
    if status_filter:
        query = query.where(Attendance.status == AttendanceStatus(status_filter))
        count_query = count_query.where(Attendance.status == AttendanceStatus(status_filter))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Attendance.date.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return PaginatedResponse(
        items=[AttendanceResponse.model_validate(r) for r in records],
        total=total, page=page, limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance(
    attendance_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    return record


@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: uuid.UUID,
    body: AttendanceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin", "teacher"))],
):
    result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

    record.status = AttendanceStatus(body.status)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    await db.delete(record)
    await db.commit()


@router.post("/mark", response_model=BulkAttendanceResponse)
async def bulk_mark_attendance(
    body: BulkAttendanceRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin", "teacher"))],
):
    """Bulk mark attendance for a batch on a given date."""
    errors = []
    marked = 0

    for record in body.records:
        # Check duplicate
        existing = await db.execute(
            select(Attendance).where(
                Attendance.student_id == record.student_id,
                Attendance.batch_id == body.batch_id,
                Attendance.date == body.date,
            )
        )
        if existing.scalar_one_or_none():
            errors.append(f"Already marked for student {record.student_id}")
            continue

        attendance = Attendance(
            student_id=record.student_id,
            batch_id=body.batch_id,
            date=body.date,
            status=AttendanceStatus(record.status),
            marked_by=current_user.id,
        )
        db.add(attendance)
        marked += 1

    await db.commit()

    return BulkAttendanceResponse(
        batch_id=body.batch_id,
        date=body.date,
        marked=marked,
        errors=errors,
    )


@router.get("/report/{batch_id}", response_model=AttendanceReportResponse)
async def get_attendance_report(
    batch_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    from_date: date_type | None = None,
    to_date: date_type | None = None,
):
    # Get batch info
    batch_result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = batch_result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    # Get enrolled students
    enrollments = await db.execute(
        select(Enrollment)
        .where(Enrollment.batch_id == batch_id)
        .options(selectinload(Enrollment.student))
    )
    enrolled = enrollments.scalars().all()

    engine = RuleEngine()
    student_reports = []
    total_percentage = 0.0

    # Count total unique class dates
    date_query = select(func.count(func.distinct(Attendance.date))).where(Attendance.batch_id == batch_id)
    if from_date:
        date_query = date_query.where(Attendance.date >= from_date)
    if to_date:
        date_query = date_query.where(Attendance.date <= to_date)
    total_classes_result = await db.execute(date_query)
    total_classes = total_classes_result.scalar() or 0

    for enrollment in enrolled:
        student = enrollment.student
        query = select(Attendance).where(
            Attendance.student_id == student.id,
            Attendance.batch_id == batch_id,
        )
        if from_date:
            query = query.where(Attendance.date >= from_date)
        if to_date:
            query = query.where(Attendance.date <= to_date)

        result = await db.execute(query)
        records = result.scalars().all()

        present = sum(1 for r in records if r.status in (AttendanceStatus.present, AttendanceStatus.late))
        absent = sum(1 for r in records if r.status == AttendanceStatus.absent)
        late = sum(1 for r in records if r.status == AttendanceStatus.late)
        total = len(records)
        pct = (present / total * 100) if total > 0 else 0.0
        total_percentage += pct

        alert = engine.evaluate_attendance_percentage(pct)
        alert_level = alert.level if alert.level != "none" else None

        student_reports.append(AttendanceStudentReport(
            student_id=student.id,
            name=student.name,
            present=present - late,
            absent=absent,
            late=late,
            percentage=round(pct, 1),
            alert_level=alert_level,
        ))

    avg_attendance = (total_percentage / len(student_reports)) if student_reports else 0.0

    return AttendanceReportResponse(
        batch_id=batch_id,
        batch_name=batch.name,
        period={
            "from": str(from_date) if from_date else None,
            "to": str(to_date) if to_date else None,
        },
        summary={
            "total_classes": total_classes,
            "average_attendance": round(avg_attendance, 1),
        },
        students=student_reports,
    )
