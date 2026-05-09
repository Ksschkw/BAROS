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
    from ....crud.vouch import get_vouch_by_job
    existing = await get_vouch_by_job(db, job.id)
    if existing:
        return existing
    from ....crud.user import get_user_by_id
    provider = await get_user_by_id(db, job.provider_id)
    if not provider or not provider.wallet_public_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider wallet not found")

    # Record vouch immediately so the client gets instant feedback
    # Underdog mint happens in background – if it fails, nft_id stays "pending"
    vouch = await create_vouch(db, job.id, current_user.id, job.provider_id, "pending", "pending")
    await db.commit()
    await db.refresh(vouch)

    # Fire-and-forget the Underdog cNFT mint
    import asyncio as _asyncio

    async def _mint_background():
        try:
            result = await mint_vouch_cnft(
                provider_wallet=provider.wallet_public_key,
                job_id=str(job.id)
            )
            nft_id = result.get("id") or result.get("mintAddress") or result.get("mint") or "pending"
            tx_sig = result.get("transactionId") or result.get("transactionSignature") or "pending"
            # Update the vouch record
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from ....core.config import settings as _s
            _engine = create_async_engine(_s.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
            _Session = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
            async with _Session() as _db:
                from sqlalchemy import update
                from ....models.vouch import Vouch
                await _db.execute(
                    update(Vouch).where(Vouch.id == vouch.id).values(cnf_nft_id=nft_id, transaction_signature=tx_sig)
                )
                await _db.commit()
            import logging as _log
            _log.getLogger(__name__).info(f"[vouches] cNFT minted for job {job.id}: {nft_id}")
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).warning(f"[vouches] Background cNFT mint failed (non-fatal): {_e}")

    _asyncio.create_task(_mint_background())

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