import httpx
from ..core.config import settings

CIVIC_API_URL = "https://api.civic.com/gateway/v1/check-gateway-token"

async def verify_civic_gateway_token(gateway_token: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            CIVIC_API_URL,
            json={"gatewayToken": gateway_token},
            headers={"Authorization": f"Bearer {settings.CIVIC_API_KEY}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("valid", False)