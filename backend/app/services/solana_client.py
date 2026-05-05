import json
import os
from typing import Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Program, Provider, Wallet, Idl
from ..core.config import settings

# Singleton pattern to avoid re‑loading the IDL and program on every request
_program: Optional[Program] = None
_client: Optional[AsyncClient] = None
_payer: Optional[Keypair] = None


def _get_payer() -> Keypair:
    global _payer
    if _payer is None:
        raw = settings.PLATFORM_KEYPAIR
        try:
            secret = json.loads(raw)       # parses the JSON array string
            _payer = Keypair.from_bytes(bytes(secret))
        except json.JSONDecodeError:
            _payer = Keypair.from_base58_string(raw)
    return _payer


async def _get_program() -> Program:
    global _program, _client
    if _program is None:
        _client = AsyncClient(settings.SOLANA_RPC_URL)
        idl_path = os.path.join(os.path.dirname(__file__), "..", "baros_program.json")
        with open(idl_path, "r") as f:
            idl = json.load(f)
        provider = Provider(_client, Wallet(_get_payer()), Confirmed)
        _program = Program(idl, idl["metadata"]["address"], provider)
    return _program


async def get_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = AsyncClient(settings.SOLANA_RPC_URL)
    return _client


async def init_escrow(
    client_pubkey: str,
    provider_pubkey: str,
    job_id: int,
    amount: int,
    client_ata: str,
    vault_ata: str,       # now required
    mint: str,
) -> str:
    program = await _get_program()
    tx = await program.rpc["init_escrow"](
        job_id,
        amount,
        ctx=program.context(
            accounts={
                "client": client_pubkey,
                "provider": provider_pubkey,
                "mint": mint,
                "clientAta": client_ata,
                "vaultAta": vault_ata,         # passed correctly
                "escrow": None,                # PDA derived by program
                "tokenProgram": Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
                "systemProgram": SYSTEM_PROGRAM_ID,
                "rent": Pubkey.from_string("SysvarRent111111111111111111111111111111111"),
            }
        ),
    )
    return str(tx)


async def release_escrow(
    client_pubkey: str,
    provider_ata: str,
    vault_ata: str,
    escrow_address: str,
) -> str:
    program = await _get_program()
    tx = await program.rpc["release_escrow"](
        ctx=program.context(
            accounts={
                "client": client_pubkey,
                "providerAta": provider_ata,
                "vaultAta": vault_ata,
                "escrow": escrow_address,
                "tokenProgram": Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
            }
        ),
    )
    return str(tx)


async def cancel_escrow(
    client_pubkey: str,
    client_ata: str,
    vault_ata: str,
    escrow_address: str,
) -> str:
    program = await _get_program()
    tx = await program.rpc["cancel_escrow"](
        ctx=program.context(
            accounts={
                "client": client_pubkey,
                "clientAta": client_ata,
                "vaultAta": vault_ata,
                "escrow": escrow_address,
                "tokenProgram": Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
            }
        ),
    )
    return str(tx)