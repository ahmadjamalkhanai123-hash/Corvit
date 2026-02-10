"""Fee routes per contracts/fees.md."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.fees import (
    FeeCreate,
    FeePaymentResponse,
    FeePayRequest,
    FeeResponse,
    FeeUpdate,
    OverdueFeeItem,
    OverdueFeeResponse,
)
from src.auth.dependencies import get_current_user, require_role
from src.database.models import Course, Fee, FeeStatus, Student, User
from src.rules.engine import RuleEngine

router = APIRouter(prefix="/fees", tags=["Fees"])


@router.post("", response_model=FeeResponse, status_code=status.HTTP_201_CREATED)
async def create_fee(
    body: FeeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    fee = Fee(
        student_id=body.student_id,
        course_id=body.course_id,
        amount=Decimal(str(body.amount)),
        due_date=body.due_date,
    )
    db.add(fee)
    await db.commit()
    await db.refresh(fee)
    return fee


@router.get("/overdue", response_model=OverdueFeeResponse)
async def get_overdue_fees(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    """Get all overdue fees."""
    today = date.today()
    engine = RuleEngine()

    result = await db.execute(
        select(Fee)
        .where(
            Fee.due_date < today,
            Fee.status.in_([FeeStatus.pending, FeeStatus.partial, FeeStatus.overdue]),
        )
        .options(selectinload(Fee.student), selectinload(Fee.course))
    )
    fees = result.scalars().all()

    items = []
    total_amount = 0.0

    for fee in fees:
        days_overdue = (today - fee.due_date).days
        alert = engine.evaluate_fee_overdue(days_overdue)
        remaining = float(fee.amount - fee.paid_amount)
        total_amount += remaining

        items.append(OverdueFeeItem(
            id=fee.id,
            student_name=fee.student.name if fee.student else "Unknown",
            course_name=fee.course.name if fee.course else "Unknown",
            amount=float(fee.amount),
            paid_amount=float(fee.paid_amount),
            due_date=fee.due_date,
            days_overdue=days_overdue,
            alert_level=alert.level,
            status="overdue",
        ))

    return OverdueFeeResponse(
        items=items,
        total_overdue_count=len(items),
        total_overdue_amount=total_amount,
    )


@router.get("", response_model=PaginatedResponse)
async def list_fees(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    student_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    sort_by: str = "due_date",
):
    query = select(Fee)
    count_query = select(func.count()).select_from(Fee)

    if student_id:
        query = query.where(Fee.student_id == student_id)
        count_query = count_query.where(Fee.student_id == student_id)
    if status_filter:
        query = query.where(Fee.status == FeeStatus(status_filter))
        count_query = count_query.where(Fee.status == FeeStatus(status_filter))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    sort_col = getattr(Fee, sort_by, Fee.due_date)
    query = query.order_by(sort_col).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    fees = result.scalars().all()

    return PaginatedResponse(
        items=[FeeResponse.model_validate(f) for f in fees],
        total=total, page=page, limit=limit,
        pages=(total + limit - 1) // limit if total else 0,
    )


@router.get("/{fee_id}", response_model=FeeResponse)
async def get_fee(
    fee_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Fee).where(Fee.id == fee_id))
    fee = result.scalar_one_or_none()
    if not fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")
    return fee


@router.put("/{fee_id}", response_model=FeeResponse)
async def update_fee(
    fee_id: uuid.UUID,
    body: FeeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Fee).where(Fee.id == fee_id))
    fee = result.scalar_one_or_none()
    if not fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")

    update_data = body.model_dump(exclude_unset=True)
    if "amount" in update_data:
        update_data["amount"] = Decimal(str(update_data["amount"]))
    if "status" in update_data:
        update_data["status"] = FeeStatus(update_data["status"])
    for key, value in update_data.items():
        setattr(fee, key, value)
    await db.commit()
    await db.refresh(fee)
    return fee


@router.delete("/{fee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee(
    fee_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Fee).where(Fee.id == fee_id))
    fee = result.scalar_one_or_none()
    if not fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")
    await db.delete(fee)
    await db.commit()


@router.post("/{fee_id}/pay", response_model=FeePaymentResponse)
async def pay_fee(
    fee_id: uuid.UUID,
    body: FeePayRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Fee).where(Fee.id == fee_id))
    fee = result.scalar_one_or_none()
    if not fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")

    remaining = fee.amount - fee.paid_amount
    payment = Decimal(str(body.amount))

    if payment > remaining:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment exceeds remaining balance",
        )

    fee.paid_amount += payment
    fee.paid_date = body.payment_date or date.today()

    if fee.paid_amount >= fee.amount:
        fee.status = FeeStatus.paid
    elif fee.paid_amount > 0:
        fee.status = FeeStatus.partial

    await db.commit()
    await db.refresh(fee)

    return FeePaymentResponse(
        id=fee.id,
        amount=float(fee.amount),
        paid_amount=float(fee.paid_amount),
        remaining=float(fee.amount - fee.paid_amount),
        status=fee.status.value,
        paid_date=fee.paid_date,
    )
