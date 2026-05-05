from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db
from ....crud.user import get_users_paginated, delete_user
from ....crud.job import get_jobs_filtered
from ....core.config import settings
router = APIRouter()

ADMIN_SECRET = settings.ADMIN_SECRET

async def verify_admin(x_admin_secret: str | None = Header(None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/users")
async def list_users(
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin),
):
    users = await get_users_paginated(db, offset=offset, limit=limit)
    return users

@router.delete("/users/{user_id}", status_code=204)
async def remove_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin),
):
    from ....crud.user import get_user_by_id
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await delete_user(db, user)
    return None

@router.get("/jobs")
async def all_jobs(
    status: str = None,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin),
):
    jobs = await get_jobs_filtered(db, status=status, limit=100)
    return jobs