"""Exam routes per contracts/exams.md."""

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.exams import (
    ExamCreate,
    ExamResponse,
    ExamResultItem,
    ExamResultsResponse,
    ExamResultStats,
    ExamResultSubmitRequest,
    ExamResultSubmitResponse,
    ExamUpdate,
)
from src.auth.dependencies import get_current_user, require_role
from src.database.models import Exam, ExamResult, ExamType, Student, User

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    body: ExamCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin", "teacher"))],
):
    exam = Exam(
        batch_id=body.batch_id,
        title=body.title,
        exam_type=ExamType(body.exam_type),
        date=body.date,
        total_marks=body.total_marks,
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)
    return exam


@router.get("", response_model=PaginatedResponse)
async def list_exams(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    batch_id: uuid.UUID | None = None,
    exam_type: str | None = None,
):
    query = select(Exam)
    count_query = select(func.count()).select_from(Exam)

    if batch_id:
        query = query.where(Exam.batch_id == batch_id)
        count_query = count_query.where(Exam.batch_id == batch_id)
    if exam_type:
        query = query.where(Exam.exam_type == ExamType(exam_type))
        count_query = count_query.where(Exam.exam_type == ExamType(exam_type))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Exam.date.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    exams = result.scalars().all()

    return PaginatedResponse(
        items=[ExamResponse.model_validate(e) for e in exams],
        total=total, page=page, limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: uuid.UUID,
    body: ExamUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin", "teacher"))],
):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    update_data = body.model_dump(exclude_unset=True)
    if "exam_type" in update_data:
        update_data["exam_type"] = ExamType(update_data["exam_type"])
    for key, value in update_data.items():
        setattr(exam, key, value)
    await db.commit()
    await db.refresh(exam)
    return exam


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    # Check for existing results
    results_count = await db.execute(
        select(func.count()).select_from(ExamResult).where(ExamResult.exam_id == exam_id)
    )
    if (results_count.scalar() or 0) > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete exam with recorded results")

    await db.delete(exam)
    await db.commit()


@router.post("/{exam_id}/results", response_model=ExamResultSubmitResponse)
async def submit_exam_results(
    exam_id: uuid.UUID,
    body: ExamResultSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin", "teacher"))],
):
    # Verify exam exists
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    errors = []
    submitted = 0

    for item in body.results:
        # Check for existing result
        existing = await db.execute(
            select(ExamResult).where(
                ExamResult.exam_id == exam_id,
                ExamResult.student_id == item.student_id,
            )
        )
        if existing.scalar_one_or_none():
            errors.append(f"Result already exists for student {item.student_id}")
            continue

        result = ExamResult(
            exam_id=exam_id,
            student_id=item.student_id,
            marks_obtained=Decimal(str(item.marks_obtained)),
            grade=item.grade,
            remarks=item.remarks,
        )
        db.add(result)
        submitted += 1

    await db.commit()

    return ExamResultSubmitResponse(
        exam_id=exam_id,
        submitted=submitted,
        errors=errors,
    )


@router.get("/{exam_id}/results", response_model=ExamResultsResponse)
async def get_exam_results(
    exam_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = exam_result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    results = await db.execute(
        select(ExamResult)
        .where(ExamResult.exam_id == exam_id)
        .options(selectinload(ExamResult.student))
    )
    result_records = results.scalars().all()

    items = []
    marks_list = []
    pass_count = 0

    for r in result_records:
        marks = float(r.marks_obtained)
        percentage = (marks / exam.total_marks * 100) if exam.total_marks > 0 else 0
        marks_list.append(marks)
        if percentage >= 40:
            pass_count += 1

        items.append(ExamResultItem(
            student_id=r.student_id,
            student_name=r.student.name if r.student else "Unknown",
            marks_obtained=marks,
            percentage=round(percentage, 1),
            grade=r.grade,
            remarks=r.remarks,
        ))

    stats = None
    if marks_list:
        stats = ExamResultStats(
            average=round(sum(marks_list) / len(marks_list), 1),
            highest=max(marks_list),
            lowest=min(marks_list),
            pass_rate=round(pass_count / len(marks_list) * 100, 1),
        )

    return ExamResultsResponse(
        exam_id=exam_id,
        exam_title=exam.title,
        total_marks=exam.total_marks,
        results=items,
        stats=stats,
    )
