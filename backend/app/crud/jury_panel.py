from uuid import UUID
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.jury_panel import JuryPanel

async def create_jury_panel(db: AsyncSession, dispute_id: UUID, juror_ids: List[UUID]) -> List[JuryPanel]:
    panels = []
    for juror_id in juror_ids:
        panel = JuryPanel(dispute_id=dispute_id, juror_id=juror_id)
        db.add(panel)
        panels.append(panel)
    await db.flush()
    return panels

async def get_jury_panel(db: AsyncSession, dispute_id: UUID) -> List[JuryPanel]:
    result = await db.execute(select(JuryPanel).where(JuryPanel.dispute_id == dispute_id))
    return result.scalars().all()

async def is_juror(db: AsyncSession, dispute_id: UUID, juror_id: UUID) -> bool:
    result = await db.execute(select(JuryPanel).where(JuryPanel.dispute_id == dispute_id, JuryPanel.juror_id == juror_id))
    return result.scalar_one_or_none() is not None