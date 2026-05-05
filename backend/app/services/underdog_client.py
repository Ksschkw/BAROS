import httpx
from ..core.config import settings

UNDERDOG_API_URL = settings.UNDERDOG_API_URL
UNDERDOG_API_KEY = settings.UNDERDOG_API_KEY


async def mint_vouch_cnft(
    provider_wallet: str,
    job_id: str,
) -> dict:
    """
    Mints a compressed NFT (vouch) to the provider's wallet.
    Returns the API response as a dict.
    """
    url = f"{UNDERDOG_API_URL}/v2/projects/baros/nfts"
    headers = {
        "Authorization": f"Bearer {UNDERDOG_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": f"BAROS Vouch - Job {job_id}",
        "symbol": "VOUCH",
        "description": "Proof of completed work on BAROS",
        "compression": True,
        "receiverAddress": provider_wallet,
        "attributes": {
            "job_id": job_id,
            "source": "baros_escrow_release",
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()