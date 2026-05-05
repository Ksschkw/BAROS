from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db, get_current_user
from ....crud.vouch import get_vouch_by_id, get_vouches_by_vouchee, create_vouch
from ....crud.job import get_job_by_id
from ....schemas.vouch import VouchCreate, VouchOut
from ....models.user import User
from ....services.underdog_client import mint_vouch_cnft
import uuid

router = APIRouter()


@router.post("/", response_model=VouchOut, status_code=status.HTTP_201_CREATED)
async def vouch_for_provider(
    vouch_data: VouchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, vouch_data.job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the client can vouch")
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job must be completed before vouching")
    # Idempotency: check if vouch already exists
    from ...crud.vouch import get_vouch_by_job
    existing = await get_vouch_by_job(db, job.id)
    if existing:
        return existing
    # Mint cNFT via Underdog
    try:
        result = await mint_vouch_cnft(provider_wallet=str(job.provider_id), job_id=str(job.id))
        nft_id = result.get("id") or result.get("mint")  # adapt based on API response
        tx_sig = result.get("transactionSignature") or "pending"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to mint vouch: {str(e)}")
    vouch = await create_vouch(db, job.id, current_user.id, job.provider_id, nft_id, tx_sig)
    return vouch


@router.get("/{vouch_id}", response_model=VouchOut)
async def get_vouch(vouch_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    vouch = await get_vouch_by_id(db, vouch_id)
    if not vouch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vouch not found")
    return vouch


@router.get("/user/{user_id}", response_model=list[VouchOut])
async def user_vouches(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await get_vouches_by_vouchee(db, user_id)