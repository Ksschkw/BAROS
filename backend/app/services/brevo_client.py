import httpx
from ..core.config import settings

BREVO_API_KEY = settings.BREVO_API_KEY
SENDER_EMAIL = settings.BREVO_SENDER_EMAIL


async def send_email(to_email: str, subject: str, html_content: str) -> dict:
    """
    Sends a transactional email via Brevo API.
    """
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "sender": {"email": SENDER_EMAIL, "name": "BAROS"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()