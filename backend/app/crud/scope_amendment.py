from uuid import UUID
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.scope_amendment import ScopeAmendment

async def get_amendment_by_id(db: AsyncSession, amendment_id: UUID) -> ScopeAmendment | None:
    result = await db.execute(select(ScopeAmendment).where(ScopeAmendment.id == amendment_id))
    return result.scalar_one_or_none()

async def get_amendments_for_job(db: AsyncSession, job_id: UUID) -> List[ScopeAmendment]:
    result = await db.execute(
        select(ScopeAmendment)
        .where(ScopeAmendment.job_id == job_id)
        .order_by(ScopeAmendment.created_at.asc())
    )
    return result.scalars().all()

async def create_amendment(
    db: AsyncSession,
    job_id: UUID,
    proposed_by: str,
    reason: str,
    new_total_price: float,
    additional_cost: float | None = None
) -> ScopeAmendment:
    amendment = ScopeAmendment(
        job_id=job_id,
        proposed_by=proposed_by,
        reason=reason,
        new_total_price=new_total_price,
        additional_cost=additional_cost,
        is_accepted=None  # pending
    )
    db.add(amendment)
    await db.commit()
    await db.refresh(amendment)
    return amendment

async def accept_amendment(db: AsyncSession, amendment: ScopeAmendment) -> ScopeAmendment:
    amendment.is_accepted = True
    await db.commit()
    await db.refresh(amendment)
    return amendment

async def reject_amendment(db: AsyncSession, amendment: ScopeAmendment) -> ScopeAmendment:
    amendment.is_accepted = False
    await db.commit()
    await db.refresh(amendment)
    return amendment