"""Dashboard route per contracts/dashboard.md: GET /api/dashboard/stats."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.auth.dependencies import get_current_user
from src.database.models import (
    Attendance,
    AttendanceStatus,
    Batch,
    BatchStatus,
    Course,
    Enrollment,
    EnrollmentStatus,
    EventLog,
    Fee,
    FeeStatus,
    Student,
    User,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    # KPIs
    total_students = (await db.execute(select(func.count()).select_from(Student))).scalar() or 0
    active_courses = (await db.execute(
        select(func.count()).select_from(Course).where(Course.is_active.is_(True))
    )).scalar() or 0
    active_batches = (await db.execute(
        select(func.count()).select_from(Batch).where(Batch.status == BatchStatus.active)
    )).scalar() or 0

    # Revenue
    total_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Fee.paid_amount), 0))
    )
    total_revenue = float(total_revenue_result.scalar() or 0)

    # Overdue fees
    from datetime import date
    today = date.today()
    overdue_result = await db.execute(
        select(func.count(), func.coalesce(func.sum(Fee.amount - Fee.paid_amount), 0))
        .where(
            Fee.due_date < today,
            Fee.status.in_([FeeStatus.pending, FeeStatus.partial, FeeStatus.overdue]),
        )
    )
    overdue_row = overdue_result.one()
    overdue_count = overdue_row[0] or 0
    overdue_amount = float(overdue_row[1] or 0)

    # Average attendance (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    total_att = (await db.execute(
        select(func.count()).select_from(Attendance).where(Attendance.date >= thirty_days_ago)
    )).scalar() or 0
    present_att = (await db.execute(
        select(func.count()).select_from(Attendance).where(
            Attendance.date >= thirty_days_ago,
            Attendance.status.in_([AttendanceStatus.present, AttendanceStatus.late]),
        )
    )).scalar() or 0
    avg_attendance = round((present_att / total_att * 100), 1) if total_att > 0 else 0.0

    # Attendance trend (last 7 days)
    attendance_trend = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_total = (await db.execute(
            select(func.count()).select_from(Attendance).where(Attendance.date == d)
        )).scalar() or 0
        day_present = (await db.execute(
            select(func.count()).select_from(Attendance).where(
                Attendance.date == d,
                Attendance.status.in_([AttendanceStatus.present, AttendanceStatus.late]),
            )
        )).scalar() or 0
        pct = round((day_present / day_total * 100), 1) if day_total > 0 else 0.0
        attendance_trend.append({"date": str(d), "percentage": pct})

    # Enrollment by course
    enrollment_by_course = []
    courses = (await db.execute(select(Course).where(Course.is_active.is_(True)))).scalars().all()
    for course in courses:
        count_result = await db.execute(
            select(func.count()).select_from(Enrollment)
            .join(Batch, Enrollment.batch_id == Batch.id)
            .where(
                Batch.course_id == course.id,
                Enrollment.status == EnrollmentStatus.active,
            )
        )
        count = count_result.scalar() or 0
        enrollment_by_course.append({"course": course.name, "count": count})

    # Recent activity (last 10 events)
    events_result = await db.execute(
        select(EventLog).order_by(EventLog.created_at.desc()).limit(10)
    )
    events = events_result.scalars().all()
    recent_activity = [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "actor": e.actor,
            "target": e.target,
            "timestamp": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

    return {
        "kpis": {
            "total_students": total_students,
            "active_courses": active_courses,
            "active_batches": active_batches,
            "total_revenue": total_revenue,
            "overdue_fees_count": overdue_count,
            "overdue_fees_amount": overdue_amount,
            "average_attendance": avg_attendance,
        },
        "attendance_trend": attendance_trend,
        "enrollment_by_course": enrollment_by_course,
        "recent_activity": recent_activity,
        "timestamp": datetime.now(UTC).isoformat(),
    }
