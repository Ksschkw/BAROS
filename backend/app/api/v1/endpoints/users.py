from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db, get_current_user
from ....crud.user import (
    get_user_by_id,
    update_user,
    update_user_location,
    delete_user,
)
from ....schemas.user import UserUpdate, UserOut, UserLocationUpdate
from ....models.user import User

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_my_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await update_user(db, current_user, updates)
    return user


@router.post("/me/location", response_model=UserOut)
async def update_my_location(
    loc: UserLocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await update_user_location(db, current_user, loc.latitude, loc.longitude)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_user(db, current_user)
    return None

@router.get("/me/wallet")
async def my_wallet(current_user: User = Depends(get_current_user)):
    return {"wallet_public_key": current_user.wallet_public_key}
    
@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id_route(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user