from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db, get_current_user
from ....crud.job import (
    get_job_by_id,
    create_job,
    assign_job,
    update_job_status,
    cancel_job_offchain,
    get_jobs_filtered,
)
from ....crud.user import get_user_by_id
from ....schemas.job import JobCreate, JobOut, JobAssign
from ....models.user import User
from ....services.solana_client import init_escrow, release_escrow, cancel_escrow
from ....core.config import settings
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from anchorpy import Program, Provider, Wallet, Idl
import uuid

# USDC Devnet mint
USDC_MINT = Pubkey.from_string(settings.USDC_MINT_DEVNET)

# Get payer keypair from config (platform wallet)
# PAYER_KEYPAIR = Keypair.from_bytes(bytes(settings.PLATFORM_KEYPAIR))

router = APIRouter()


# def _get_user_keypair(user: User) -> Keypair:
#     """Decrypt user's private key from DB."""
#     from cryptography.fernet import Fernet
#     f = Fernet(settings.WALLET_ENCRYPTION_KEY)
#     secret = f.decrypt(user._wallet_private_key.encode()).decode()
#     return Keypair.from_base58_string(secret)

def _get_user_keypair(user: User) -> Keypair:
    from cryptography.fernet import Fernet
    f = Fernet(settings.WALLET_ENCRYPTION_KEY.encode())
    secret = f.decrypt(user._wallet_private_key.encode()).decode()
    return Keypair.from_base58_string(secret)

@router.post("/", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job_route(
    job_in: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await create_job(db, current_user.id, job_in)
    return job


@router.get("/{job_id}", response_model=JobOut)
async def get_job_route(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.get("/", response_model=list[JobOut])
async def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius: float = Query(10.0),
    category_id: Optional[str] = Query(None),
    my: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_id = None
    provider_id = None
    if my == "client":
        client_id = current_user.id
    elif my == "provider":
        provider_id = current_user.id

    return await get_jobs_filtered(
        db,
        client_id=client_id,
        provider_id=provider_id,
        status=status_filter,
        category_id=uuid.UUID(category_id) if category_id else None,
        latitude=lat,
        longitude=lon,
        radius_km=radius,
    )


@router.post("/{job_id}/assign", response_model=JobOut)
async def assign_job_route(
    job_id: uuid.UUID,
    assign_data: JobAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the client can assign")
    if job.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not open")
    job = await assign_job(db, job, assign_data.provider_id)
    return job


@router.post("/{job_id}/fund", response_model=JobOut)
async def fund_job_route(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the client can fund")
    if job.status != "assigned":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job must be assigned before funding")

    # Idempotency: if already funded, return current state
    if job.status == "funded":
        return job

    # Get client and provider keypairs
    client_user = current_user
    client_kp = _get_user_keypair(client_user)
    provider_user = await get_user_by_id(db, job.provider_id)
    if not provider_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    provider_pubkey = Pubkey.from_string(provider_user.wallet_public_key)

    # Derive ATAs
    client_ata = Pubkey.find_program_address(
        [bytes(client_kp.pubkey()), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    # Escrow PDA (program will derive vault_ata from seeds in the contract)
    # We just call the contract and it will create the escrow account and vault_ata
    try:
        tx_sig = await init_escrow(
            client_pubkey=str(client_kp.pubkey()),
            provider_pubkey=str(provider_pubkey),
            job_id=int(job.id),  # careful: job.id is UUID, convert to int for u64? We'll use hash or store a numeric ID
            amount=int(job.price * 10**6),  # USDC has 6 decimals
            client_ata=str(client_ata),
            vault_ata=None,  # will be derived by program
            mint=str(USDC_MINT),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solana transaction failed: {str(e)}")

    # Derive escrow PDA for later use (seeds: b"escrow", client_pubkey, job_id.to_le_bytes())
    # We'll recalculate it the same way the contract does: seeds = [b"escrow", client_pubkey, &job_id.to_le_bytes()]
    # The job_id in the contract is a u64, but our job.id is UUID. We need to map UUID to a u64 consistently.
    # For now, we'll store the transaction sig and derive the escrow address later.
    # Better: store a numeric job serial ID in the database (auto-increment). Let's convert UUID to int by hashing.
    # Simpler: Add a numeric field `on_chain_id` to Job model that is unique. We'll generate it sequentially.
    # Hackathon approach: use the UUID's integer representation from .int (128 bits) -> but u64 is 64 bits. We'll take lower 64 bits.
    job_id_int = job.id.int & 0xFFFFFFFFFFFFFFFF  # truncate to u64
    escrow_pubkey = Pubkey.find_program_address(
        [b"escrow", bytes(client_kp.pubkey()), job_id_int.to_bytes(8, 'little')],
        Pubkey.from_string(settings.BAROS_PROGRAM_ID)
    )[0]

    job = await update_job_status(db, job, "funded", escrow_address=str(escrow_pubkey))
    return job


@router.post("/{job_id}/release", response_model=JobOut)
async def release_job_route(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the client can release")
    if job.status != "funded":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not in funded state")

    # Idempotency
    if job.status == "completed":
        return job

    client_user = current_user
    provider_user = await get_user_by_id(db, job.provider_id)
    provider_pubkey = Pubkey.from_string(provider_user.wallet_public_key)

    # Derive the escrow PDA (same as fund)
    job_id_int = job.id.int & 0xFFFFFFFFFFFFFFFF
    escrow_pubkey = Pubkey.find_program_address(
        [b"escrow", bytes(Pubkey.from_string(client_user.wallet_public_key)), job_id_int.to_bytes(8, 'little')],
        Pubkey.from_string(settings.BAROS_PROGRAM_ID)
    )[0]

    # Derive vault ATA owned by escrow PDA
    vault_ata = Pubkey.find_program_address(
        [bytes(escrow_pubkey), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    # Provider ATA
    provider_ata = Pubkey.find_program_address(
        [bytes(provider_pubkey), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    try:
        tx_sig = await release_escrow(
            client_pubkey=str(Pubkey.from_string(client_user.wallet_public_key)),
            provider_ata=str(provider_ata),
            vault_ata=str(vault_ata),
            escrow_address=str(escrow_pubkey),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solana transaction failed: {str(e)}")

    job = await update_job_status(db, job, "completed")
    return job


@router.post("/{job_id}/cancel", response_model=JobOut)
async def cancel_job_route(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.client_id != current_user.id and job.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only involved parties can cancel")
    if job.status in ("completed", "cancelled", "disputed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job cannot be cancelled")

    # Pre-funding cancellation (either party)
    if job.status not in ("funded", "in_progress"):
        job = await cancel_job_offchain(db, job)
        return job

    # Post-funding: only client can cancel on-chain
    if job.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only client can cancel after funding")

    client_user = current_user
    job_id_int = job.id.int & 0xFFFFFFFFFFFFFFFF
    escrow_pubkey = Pubkey.find_program_address(
        [b"escrow", bytes(Pubkey.from_string(client_user.wallet_public_key)), job_id_int.to_bytes(8, 'little')],
        Pubkey.from_string(settings.BAROS_PROGRAM_ID)
    )[0]

    vault_ata = Pubkey.find_program_address(
        [bytes(escrow_pubkey), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    # Client ATA for refund
    client_ata = Pubkey.find_program_address(
        [bytes(Pubkey.from_string(client_user.wallet_public_key)), bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")), bytes(USDC_MINT)],
        Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    )[0]

    try:
        tx_sig = await cancel_escrow(
            client_pubkey=str(Pubkey.from_string(client_user.wallet_public_key)),
            client_ata=str(client_ata),
            vault_ata=str(vault_ata),
            escrow_address=str(escrow_pubkey),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Solana transaction failed: {str(e)}")

    job = await update_job_status(db, job, "cancelled")
    return job