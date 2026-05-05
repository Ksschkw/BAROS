from uuid import UUID
from typing import List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.message import Message

async def get_message_by_id(db: AsyncSession, message_id: UUID) -> Message | None:
    result = await db.execute(select(Message).where(Message.id == message_id))
    return result.scalar_one_or_none()

async def get_messages_for_job(
    db: AsyncSession,
    job_id: UUID,
    limit: int = 50,
    offset: int = 0
) -> List[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.job_id == job_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()

async def get_messages_for_job_since(
    db: AsyncSession,
    job_id: UUID,
    since_id: UUID | None = None,
    limit: int = 50
) -> List[Message]:
    query = select(Message).where(Message.job_id == job_id).order_by(Message.created_at.asc())
    if since_id:
        # Fetch messages after the given id (simple cursor)
        sub = select(Message.created_at).where(Message.id == since_id).scalar_subquery()
        query = query.where(Message.created_at > sub)
    result = await db.execute(query.limit(limit))
    return result.scalars().all()

async def create_message(
    db: AsyncSession,
    job_id: UUID,
    sender_id: UUID,
    content: str
) -> Message:
    message = Message(
        job_id=job_id,
        sender_id=sender_id,
        content=content,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

async def delete_message(db: AsyncSession, message: Message) -> None:
    await db.delete(message)
    await db.commit()