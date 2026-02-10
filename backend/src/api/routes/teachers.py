"""Teacher routes per contracts/teachers.md."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.teachers import (
    TeacherBatchesResponse,
    TeacherBatchItem,
    TeacherCreate,
    TeacherResponse,
    TeacherUpdate,
)
from src.auth.dependencies import get_current_user, require_role
from src.database.models import Batch, BatchStatus, Enrollment, Teacher, User

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    body: TeacherCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    existing = await db.execute(select(Teacher).where(Teacher.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    teacher = Teacher(**body.model_dump())
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)
    return teacher


@router.get("", response_model=PaginatedResponse)
async def list_teachers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None,
):
    query = select(Teacher)
    count_query = select(func.count()).select_from(Teacher)

    if search:
        query = query.where(Teacher.name.ilike(f"%{search}%"))
        count_query = count_query.where(Teacher.name.ilike(f"%{search}%"))
    if is_active is not None:
        query = query.where(Teacher.is_active == is_active)
        count_query = count_query.where(Teacher.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Teacher.name).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    teachers = result.scalars().all()

    return PaginatedResponse(
        items=[TeacherResponse.model_validate(t) for t in teachers],
        total=total, page=page, limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: uuid.UUID,
    body: TeacherUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(teacher, key, value)
    await db.commit()
    await db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    teacher_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    active_batches = await db.execute(
        select(func.count()).select_from(Batch).where(
            Batch.teacher_id == teacher_id,
            Batch.status == BatchStatus.active,
        )
    )
    if (active_batches.scalar() or 0) > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete teacher with active batches")

    await db.delete(teacher)
    await db.commit()


@router.get("/{teacher_id}/batches", response_model=TeacherBatchesResponse)
async def get_teacher_batches(
    teacher_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Batch)
        .where(Batch.teacher_id == teacher_id)
        .options(selectinload(Batch.course), selectinload(Batch.enrollments))
    )
    batches = result.scalars().all()

    batch_items = []
    for b in batches:
        student_count = len([e for e in b.enrollments if e.status.value == "active"])
        batch_items.append(TeacherBatchItem(
            id=b.id,
            name=b.name,
            course_name=b.course.name if b.course else "",
            schedule_days=b.schedule_days,
            schedule_time=b.schedule_time,
            student_count=student_count,
            status=b.status.value,
        ))

    return TeacherBatchesResponse(teacher_id=teacher_id, batches=batch_items)
