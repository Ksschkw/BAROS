from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.vote import Vote, VoteOption
from typing import List

async def create_vote(db: AsyncSession, dispute_id: UUID, juror_id: UUID, vote: VoteOption) -> Vote:
    v = Vote(dispute_id=dispute_id, juror_id=juror_id, vote=vote)
    db.add(v)
    await db.flush()
    return v

async def get_votes_for_dispute(db: AsyncSession, dispute_id: UUID) -> List[Vote]:
    result = await db.execute(select(Vote).where(Vote.dispute_id == dispute_id))
    return result.scalars().all()