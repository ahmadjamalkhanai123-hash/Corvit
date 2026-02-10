"""Enrollment routes per contracts/enrollments.md."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.enrollments import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentUpdate,
)
from src.auth.dependencies import get_current_user, require_role
from src.database.models import Batch, Enrollment, EnrollmentStatus, EventLog, User

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


async def _build_enrollment_response(enrollment: Enrollment) -> EnrollmentResponse:
    resp = EnrollmentResponse.model_validate(enrollment)
    resp.student_name = enrollment.student.name if enrollment.student else None
    resp.batch_name = enrollment.batch.name if enrollment.batch else None
    resp.course_name = enrollment.batch.course.name if enrollment.batch and enrollment.batch.course else None
    return resp


@router.post("", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    body: EnrollmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    # Check duplicate
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == body.student_id,
            Enrollment.batch_id == body.batch_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already enrolled in this batch")

    # Check capacity
    batch_result = await db.execute(select(Batch).where(Batch.id == body.batch_id))
    batch = batch_result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    enrolled_count = await db.execute(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.batch_id == body.batch_id,
            Enrollment.status == EnrollmentStatus.active,
        )
    )
    if (enrolled_count.scalar() or 0) >= batch.max_capacity:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Batch is at maximum capacity")

    enrollment = Enrollment(**body.model_dump())
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment, attribute_names=["student", "batch"])
    # Eagerly load batch.course
    if enrollment.batch:
        await db.refresh(enrollment.batch, attribute_names=["course"])
    return await _build_enrollment_response(enrollment)


@router.get("", response_model=PaginatedResponse)
async def list_enrollments(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    student_id: uuid.UUID | None = None,
    batch_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
):
    query = select(Enrollment).options(
        selectinload(Enrollment.student),
        selectinload(Enrollment.batch).selectinload(Batch.course),
    )
    count_query = select(func.count()).select_from(Enrollment)

    if student_id:
        query = query.where(Enrollment.student_id == student_id)
        count_query = count_query.where(Enrollment.student_id == student_id)
    if batch_id:
        query = query.where(Enrollment.batch_id == batch_id)
        count_query = count_query.where(Enrollment.batch_id == batch_id)
    if status_filter:
        query = query.where(Enrollment.status == EnrollmentStatus(status_filter))
        count_query = count_query.where(Enrollment.status == EnrollmentStatus(status_filter))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Enrollment.enrollment_date.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    enrollments = result.scalars().all()

    items = [await _build_enrollment_response(e) for e in enrollments]

    return PaginatedResponse(
        items=items, total=total, page=page, limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    enrollment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Enrollment).where(Enrollment.id == enrollment_id)
        .options(
            selectinload(Enrollment.student),
            selectinload(Enrollment.batch).selectinload(Batch.course),
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return await _build_enrollment_response(enrollment)


@router.put("/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: uuid.UUID,
    body: EnrollmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(
        select(Enrollment).where(Enrollment.id == enrollment_id)
        .options(
            selectinload(Enrollment.student),
            selectinload(Enrollment.batch).selectinload(Batch.course),
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = EnrollmentStatus(update_data["status"])
    for key, value in update_data.items():
        setattr(enrollment, key, value)
    await db.commit()
    await db.refresh(enrollment)
    return await _build_enrollment_response(enrollment)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enrollment(
    enrollment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    await db.delete(enrollment)
    await db.commit()


@router.post("/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    body: EnrollmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
):
    """Convenience enrollment endpoint with event logging."""
    # Reuse create logic
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == body.student_id,
            Enrollment.batch_id == body.batch_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already enrolled in this batch")

    batch_result = await db.execute(
        select(Batch).where(Batch.id == body.batch_id).options(selectinload(Batch.course))
    )
    batch = batch_result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    enrolled_count = await db.execute(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.batch_id == body.batch_id,
            Enrollment.status == EnrollmentStatus.active,
        )
    )
    if (enrolled_count.scalar() or 0) >= batch.max_capacity:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Batch is at maximum capacity")

    enrollment = Enrollment(**body.model_dump())
    db.add(enrollment)

    # Log event
    event = EventLog(
        event_type="enrollment",
        actor=current_user.username,
        target=f"{body.student_id} -> {batch.name}",
        details={"student_id": str(body.student_id), "batch_id": str(body.batch_id)},
    )
    db.add(event)

    await db.commit()
    await db.refresh(enrollment, attribute_names=["student", "batch"])
    if enrollment.batch:
        await db.refresh(enrollment.batch, attribute_names=["course"])
    return await _build_enrollment_response(enrollment)
