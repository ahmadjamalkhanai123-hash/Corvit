"""Fee evaluation for individual students."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Fee, FeeStatus
from src.rules.engine import AlertResult, RuleEngine


async def evaluate_fees(
    session: AsyncSession,
    student_id: uuid.UUID,
    engine: RuleEngine | None = None,
) -> AlertResult:
    """Evaluate a student's fee status and return the highest alert level."""
    if engine is None:
        engine = RuleEngine()

    query = select(Fee).where(
        Fee.student_id == student_id,
        Fee.status.in_([FeeStatus.pending, FeeStatus.partial, FeeStatus.overdue]),
    )
    result = await session.execute(query)
    fees = result.scalars().all()

    if not fees:
        return AlertResult(level="none", message="All fees are paid.")

    today = date.today()
    severity = {"none": 0, "yellow": 1, "orange": 2, "red": 3}
    worst_alert = AlertResult(level="none", message="No overdue fees.")

    for fee in fees:
        days_overdue = (today - fee.due_date).days
        if days_overdue <= 0:
            continue
        alert = engine.evaluate_fee_overdue(days_overdue)
        if severity.get(alert.level, 0) > severity.get(worst_alert.level, 0):
            worst_alert = AlertResult(
                level=alert.level,
                message=alert.message,
                details={"days_overdue": days_overdue, "fee_id": str(fee.id), "amount_due": float(fee.amount - fee.paid_amount)},
            )

    return worst_alert
