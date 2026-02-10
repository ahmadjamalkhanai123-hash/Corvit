"""DB action functions for the Director Agent."""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    Attendance,
    AttendanceStatus,
    Batch,
    Enrollment,
    EnrollmentStatus,
    EventLog,
    Fee,
    FeeStatus,
    Student,
)


async def enroll_student(
    session: AsyncSession,
    student_id: uuid.UUID,
    batch_id: uuid.UUID,
) -> dict[str, Any]:
    """Enroll a student in a batch."""
    # Check if already enrolled
    existing = await session.execute(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.batch_id == batch_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"success": False, "error": "Student already enrolled in this batch"}

    # Check capacity
    batch_result = await session.execute(
        select(Batch).where(Batch.id == batch_id).options(selectinload(Batch.course))
    )
    batch = batch_result.scalar_one_or_none()
    if not batch:
        return {"success": False, "error": "Batch not found"}

    count_result = await session.execute(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.batch_id == batch_id,
            Enrollment.status == EnrollmentStatus.active,
        )
    )
    if (count_result.scalar() or 0) >= batch.max_capacity:
        return {"success": False, "error": "Batch is at maximum capacity"}

    enrollment = Enrollment(student_id=student_id, batch_id=batch_id)
    session.add(enrollment)
    await session.commit()

    return {
        "success": True,
        "enrollment_id": str(enrollment.id),
        "batch_name": batch.name,
        "course_name": batch.course.name if batch.course else None,
    }


async def check_fees(
    session: AsyncSession,
    student_id: uuid.UUID,
) -> dict[str, Any]:
    """Check fee status for a student."""
    result = await session.execute(
        select(Fee)
        .where(Fee.student_id == student_id)
        .options(selectinload(Fee.course))
    )
    fees = result.scalars().all()

    today = date.today()
    fee_list = []
    total_due = 0.0
    total_paid = 0.0

    for fee in fees:
        remaining = float(fee.amount - fee.paid_amount)
        if remaining > 0:
            total_due += remaining
        total_paid += float(fee.paid_amount)
        days_overdue = max(0, (today - fee.due_date).days)

        fee_list.append({
            "course": fee.course.name if fee.course else "Unknown",
            "amount": float(fee.amount),
            "paid": float(fee.paid_amount),
            "remaining": remaining,
            "due_date": str(fee.due_date),
            "days_overdue": days_overdue,
            "status": fee.status.value,
        })

    return {
        "fees": fee_list,
        "total_due": total_due,
        "total_paid": total_paid,
    }


async def get_attendance_summary(
    session: AsyncSession,
    student_id: uuid.UUID,
    batch_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Get attendance summary for a student."""
    query = select(Attendance).where(Attendance.student_id == student_id)
    if batch_id:
        query = query.where(Attendance.batch_id == batch_id)

    result = await session.execute(query)
    records = result.scalars().all()

    total = len(records)
    present = sum(1 for r in records if r.status in (AttendanceStatus.present, AttendanceStatus.late))
    absent = sum(1 for r in records if r.status == AttendanceStatus.absent)
    late = sum(1 for r in records if r.status == AttendanceStatus.late)
    percentage = (present / total * 100) if total > 0 else 0.0

    return {
        "total_classes": total,
        "present": present,
        "absent": absent,
        "late": late,
        "percentage": round(percentage, 1),
    }


async def log_event(
    session: AsyncSession,
    event_type: str,
    actor: str,
    target: str | None = None,
    details: dict | None = None,
) -> None:
    """Log an event to the event log."""
    event = EventLog(
        event_type=event_type,
        actor=actor,
        target=target,
        details=details,
    )
    session.add(event)
    await session.commit()
