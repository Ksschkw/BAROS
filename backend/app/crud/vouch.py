from uuid import UUID
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.vouch import Vouch

async def get_vouch_by_id(db: AsyncSession, vouch_id: UUID) -> Vouch | None:
    result = await db.execute(select(Vouch).where(Vouch.id == vouch_id))
    return result.scalar_one_or_none()

async def get_vouches_by_vouchee(db: AsyncSession, vouchee_id: UUID, limit: int = 50, offset: int = 0) -> List[Vouch]:
    result = await db.execute(
        select(Vouch)
        .where(Vouch.vouchee_id == vouchee_id)
        .order_by(Vouch.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()

async def get_vouch_by_job(db: AsyncSession, job_id: UUID) -> Vouch | None:
    result = await db.execute(select(Vouch).where(Vouch.job_id == job_id))
    return result.scalar_one_or_none()

async def create_vouch(
    db: AsyncSession,
    job_id: UUID,
    voucher_id: UUID,
    vouchee_id: UUID,
    cnf_nft_id: str,
    transaction_signature: str
) -> Vouch:
    vouch = Vouch(
        job_id=job_id,
        voucher_id=voucher_id,
        vouchee_id=vouchee_id,
        cnf_nft_id=cnf_nft_id,
        transaction_signature=transaction_signature,
    )
    db.add(vouch)
    await db.commit()
    await db.refresh(vouch)
    return vouch