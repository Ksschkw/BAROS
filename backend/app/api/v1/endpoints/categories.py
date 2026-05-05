from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db
from ....crud.category import list_categories, create_category, get_category_by_name
from ....schemas.category import CategoryCreate, CategoryOut

router = APIRouter()


@router.get("/", response_model=list[CategoryOut])
async def get_categories(db: AsyncSession = Depends(get_db)):
    return await list_categories(db)


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def add_category(cat: CategoryCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_category_by_name(db, cat.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")
    return await create_category(db, cat.name)