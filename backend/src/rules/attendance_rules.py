"""Attendance evaluation for individual students."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Attendance, AttendanceStatus
from src.rules.engine import AlertResult, RuleEngine


async def evaluate_attendance(
    session: AsyncSession,
    student_id: uuid.UUID,
    batch_id: uuid.UUID,
    engine: RuleEngine | None = None,
) -> AlertResult:
    """Evaluate a student's attendance in a batch and return alert level."""
    if engine is None:
        engine = RuleEngine()

    # Total classes
    total_q = select(func.count()).where(
        Attendance.student_id == student_id,
        Attendance.batch_id == batch_id,
    )
    total_result = await session.execute(total_q)
    total = total_result.scalar() or 0

    if total == 0:
        return AlertResult(level="none", message="No attendance records found.")

    # Present + late count as attended
    present_q = select(func.count()).where(
        Attendance.student_id == student_id,
        Attendance.batch_id == batch_id,
        Attendance.status.in_([AttendanceStatus.present, AttendanceStatus.late]),
    )
    present_result = await session.execute(present_q)
    present = present_result.scalar() or 0

    percentage = (present / total) * 100

    # Check percentage threshold
    pct_alert = engine.evaluate_attendance_percentage(percentage)

    # Check consecutive absences
    recent_q = (
        select(Attendance.status)
        .where(
            Attendance.student_id == student_id,
            Attendance.batch_id == batch_id,
        )
        .order_by(Attendance.date.desc())
        .limit(10)
    )
    recent_result = await session.execute(recent_q)
    recent_statuses = [row[0] for row in recent_result.fetchall()]

    consecutive = 0
    for s in recent_statuses:
        if s == AttendanceStatus.absent:
            consecutive += 1
        else:
            break

    consec_alert = engine.evaluate_consecutive_absences(consecutive)

    # Return the more severe alert
    severity = {"none": 0, "yellow": 1, "orange": 2, "red": 3}
    if severity.get(consec_alert.level, 0) > severity.get(pct_alert.level, 0):
        return consec_alert
    return pct_alert
