from uuid import UUID
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.category import Category

async def get_category_by_id(db: AsyncSession, category_id: UUID) -> Category | None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalar_one_or_none()

async def get_category_by_name(db: AsyncSession, name: str) -> Category | None:
    result = await db.execute(select(Category).where(Category.name == name))
    return result.scalar_one_or_none()

async def list_categories(db: AsyncSession) -> List[Category]:
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()

async def create_category(db: AsyncSession, name: str) -> Category:
    category = Category(name=name)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

async def delete_category(db: AsyncSession, category: Category) -> None:
    await db.delete(category)
    await db.commit()