"""Course routes per contracts/courses.md."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.courses import (
    CourseBatchesResponse,
    CourseBatchItem,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
)
from src.auth.dependencies import get_current_user, require_role
from src.database.models import Batch, BatchStatus, Course, User

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    body: CourseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    existing = await db.execute(select(Course).where(Course.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course code already exists")

    course = Course(**body.model_dump())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("", response_model=PaginatedResponse)
async def list_courses(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category: str | None = None,
    is_active: bool | None = None,
):
    query = select(Course)
    count_query = select(func.count()).select_from(Course)

    if search:
        query = query.where(Course.name.ilike(f"%{search}%"))
        count_query = count_query.where(Course.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Course.category == category)
        count_query = count_query.where(Course.category == category)
    if is_active is not None:
        query = query.where(Course.is_active == is_active)
        count_query = count_query.where(Course.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Course.name).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()

    return PaginatedResponse(
        items=[CourseResponse.model_validate(c) for c in courses],
        total=total, page=page, limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: uuid.UUID,
    body: CourseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    active_batches = await db.execute(
        select(func.count()).select_from(Batch).where(
            Batch.course_id == course_id,
            Batch.status == BatchStatus.active,
        )
    )
    if (active_batches.scalar() or 0) > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete course with active batches")

    await db.delete(course)
    await db.commit()


@router.get("/{course_id}/batches", response_model=CourseBatchesResponse)
async def get_course_batches(
    course_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    batches_result = await db.execute(
        select(Batch)
        .where(Batch.course_id == course_id)
        .options(selectinload(Batch.teacher), selectinload(Batch.enrollments))
    )
    batches = batches_result.scalars().all()

    batch_items = []
    for b in batches:
        enrolled = len([e for e in b.enrollments if e.status.value == "active"])
        batch_items.append(CourseBatchItem(
            id=b.id,
            name=b.name,
            teacher_name=b.teacher.name if b.teacher else "",
            schedule_days=b.schedule_days,
            schedule_time=b.schedule_time,
            start_date=str(b.start_date) if b.start_date else None,
            enrolled=enrolled,
            max_capacity=b.max_capacity,
            seats_available=b.max_capacity - enrolled,
            status=b.status.value,
        ))

    return CourseBatchesResponse(
        course_id=course_id,
        course_name=course.name,
        batches=batch_items,
    )
