"""Batch routes per contracts/batches.md."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.batches import (
    BatchCreate,
    BatchResponse,
    BatchScheduleResponse,
    BatchStudentItem,
    BatchStudentsResponse,
    BatchUpdate,
)
from src.api.schemas.common import PaginatedResponse
from src.auth.dependencies import get_current_user, require_role
from src.database.models import (
    Attendance,
    AttendanceStatus,
    Batch,
    BatchStatus,
    Enrollment,
    EnrollmentStatus,
    User,
)

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    body: BatchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    batch = Batch(**body.model_dump())
    db.add(batch)
    await db.commit()
    await db.refresh(batch, attribute_names=["course", "teacher"])
    resp = BatchResponse.model_validate(batch)
    resp.course_name = batch.course.name if batch.course else None
    resp.teacher_name = batch.teacher.name if batch.teacher else None
    return resp


@router.get("", response_model=PaginatedResponse)
async def list_batches(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    course_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
):
    query = select(Batch).options(selectinload(Batch.course), selectinload(Batch.teacher))
    count_query = select(func.count()).select_from(Batch)

    if course_id:
        query = query.where(Batch.course_id == course_id)
        count_query = count_query.where(Batch.course_id == course_id)
    if teacher_id:
        query = query.where(Batch.teacher_id == teacher_id)
        count_query = count_query.where(Batch.teacher_id == teacher_id)
    if status_filter:
        query = query.where(Batch.status == BatchStatus(status_filter))
        count_query = count_query.where(Batch.status == BatchStatus(status_filter))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Batch.name).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    batches = result.scalars().all()

    items = []
    for b in batches:
        resp = BatchResponse.model_validate(b)
        resp.course_name = b.course.name if b.course else None
        resp.teacher_name = b.teacher.name if b.teacher else None
        items.append(resp)

    return PaginatedResponse(
        items=items, total=total, page=page, limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id)
        .options(selectinload(Batch.course), selectinload(Batch.teacher))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    resp = BatchResponse.model_validate(batch)
    resp.course_name = batch.course.name if batch.course else None
    resp.teacher_name = batch.teacher.name if batch.teacher else None
    return resp


@router.put("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: uuid.UUID,
    body: BatchUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id)
        .options(selectinload(Batch.course), selectinload(Batch.teacher))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = BatchStatus(update_data["status"])
    for key, value in update_data.items():
        setattr(batch, key, value)
    await db.commit()
    await db.refresh(batch)
    resp = BatchResponse.model_validate(batch)
    resp.course_name = batch.course.name if batch.course else None
    resp.teacher_name = batch.teacher.name if batch.teacher else None
    return resp


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    batch_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    active = await db.execute(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.batch_id == batch_id,
            Enrollment.status == EnrollmentStatus.active,
        )
    )
    if (active.scalar() or 0) > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete batch with active enrollments")

    await db.delete(batch)
    await db.commit()


@router.get("/{batch_id}/students", response_model=BatchStudentsResponse)
async def get_batch_students(
    batch_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    enrollments_result = await db.execute(
        select(Enrollment)
        .where(Enrollment.batch_id == batch_id)
        .options(selectinload(Enrollment.student))
    )
    enrollments = enrollments_result.scalars().all()

    students = []
    for e in enrollments:
        s = e.student
        # Calculate attendance percentage
        total_q = await db.execute(
            select(func.count()).select_from(Attendance).where(
                Attendance.student_id == s.id, Attendance.batch_id == batch_id
            )
        )
        total = total_q.scalar() or 0
        present_q = await db.execute(
            select(func.count()).select_from(Attendance).where(
                Attendance.student_id == s.id, Attendance.batch_id == batch_id,
                Attendance.status.in_([AttendanceStatus.present, AttendanceStatus.late]),
            )
        )
        present = present_q.scalar() or 0
        pct = (present / total * 100) if total > 0 else None

        students.append(BatchStudentItem(
            id=s.id, name=s.name, email=s.email,
            enrollment_status=e.status.value,
            attendance_percentage=round(pct, 1) if pct is not None else None,
        ))

    return BatchStudentsResponse(
        batch_id=batch_id, batch_name=batch.name,
        students=students, total_enrolled=len(students),
    )


@router.get("/{batch_id}/schedule", response_model=BatchScheduleResponse)
async def get_batch_schedule(
    batch_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Batch).where(Batch.id == batch_id)
        .options(selectinload(Batch.course), selectinload(Batch.teacher))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    return BatchScheduleResponse(
        batch_id=batch.id,
        batch_name=batch.name,
        course_name=batch.course.name if batch.course else "",
        teacher_name=batch.teacher.name if batch.teacher else "",
        room=batch.room,
        schedule_days=batch.schedule_days,
        schedule_time=batch.schedule_time,
        start_date=batch.start_date,
        end_date=batch.end_date,
    )
