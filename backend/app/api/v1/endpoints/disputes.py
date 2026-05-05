from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db, get_current_user
from ....crud.dispute import (
    get_dispute_by_id,
    get_dispute_by_job,
    create_dispute,
    resolve_dispute,
)
from ....crud.job import get_job_by_id, update_job_status
from ....crud.user import get_user_by_id
from ....schemas.dispute import DisputeCreate, DisputeResolve, DisputeOut
from ....models.user import User
from ....services.solana_client import release_escrow, cancel_escrow
from ....core.config import settings
from solders.pubkey import Pubkey
import uuid
from ....models.job import Job

router = APIRouter()

USDC_MINT = Pubkey.from_string(settings.USDC_MINT_DEVNET)

ADMIN_SECRET = "baros_admin_secret_2026"


async def verify_admin(x_admin_secret: str | None = Header(None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return True


@router.post("/", response_model=DisputeOut, status_code=status.HTTP_201_CREATED)
async def raise_dispute(
    dispute_data: DisputeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, dispute_data.job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.client_id != current_user.id and job.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only involved parties can dispute")
    if job.status == "disputed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dispute already exists")
    if job.status not in ("funded", "in_progress"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only dispute an active job")
    await update_job_status(db, job, "disputed")
    dispute = await create_dispute(db, job.client_id, job.provider_id, dispute_data)
    return dispute


@router.get("/{dispute_id}", response_model=DisputeOut)
async def get_dispute(dispute_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    dispute = await get_dispute_by_id(db, dispute_id)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")
    return dispute


@router.post("/{dispute_id}/resolve", response_model=DisputeOut)
async def resolve_dispute_route(
    dispute_id: uuid.UUID,
    resolution_data: DisputeResolve,
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    dispute = await get_dispute_by_id(db, dispute_id)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")
    if dispute.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dispute already resolved")

    job = await get_job_by_id(db, dispute.job_id)
    if not job or job.status != "disputed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not in disputed state")

    client_user = await get_user_by_id(db, job.client_id)
    provider_user = await get_user_by_id(db, job.provider_id)

    escrow_pubkey = Pubkey.find_program_address(
        [b"escrow", bytes(Pubkey.from_string(client_user.wallet_public_key)), int(job.contract_job_id, 16).to_bytes(8, 'little')],
        Pubkey.from_string(settings.BAROS_PROGRAM_ID)
    )[0]

    vault_ata = Pubkey.find_program_address(
        [bytes(escrow_pubkey), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    client_ata = Pubkey.find_program_address(
        [bytes(Pubkey.from_string(client_user.wallet_public_key)), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    provider_ata = Pubkey.find_program_address(
        [bytes(Pubkey.from_string(provider_user.wallet_public_key)), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    try:
        if resolution_data.resolution == "refund":
            tx = await cancel_escrow(
                client_pubkey=str(Pubkey.from_string(client_user.wallet_public_key)),
                client_ata=str(client_ata),
                vault_ata=str(vault_ata),
                escrow_address=str(escrow_pubkey),
            )
            await update_job_status(db, job, "cancelled")
        elif resolution_data.resolution == "release":
            tx = await release_escrow(
                client_pubkey=str(Pubkey.from_string(client_user.wallet_public_key)),
                provider_ata=str(provider_ata),
                vault_ata=str(vault_ata),
                escrow_address=str(escrow_pubkey),
            )
            await update_job_status(db, job, "completed")
        else:
            tx = await release_escrow(
                client_pubkey=str(Pubkey.from_string(client_user.wallet_public_key)),
                provider_ata=str(provider_ata),
                vault_ata=str(vault_ata),
                escrow_address=str(escrow_pubkey),
            )
            await update_job_status(db, job, "completed")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solana transaction failed: {str(e)}")

    dispute = await resolve_dispute(db, dispute, resolution_data.resolution)
    return dispute