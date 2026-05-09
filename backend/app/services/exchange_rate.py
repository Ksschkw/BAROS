"""
Exchange rate service — fetches NGN/USD rate from open.er-api.com.
Free, no API key required. Rate is cached in memory for 60 minutes.
"""
import time
import logging
import httpx

logger = logging.getLogger(__name__)

# In-memory cache: { "rate": float, "fetched_at": float (epoch seconds) }
_cache: dict = {}
_CACHE_TTL = 3600  # 60 minutes


async def get_ngn_usd_rate() -> float:
    """
    Return the current NGN-per-USD exchange rate.
    Result is cached for 60 minutes to avoid hammering the free API.
    Falls back to 1600.0 if the API is unreachable.
    """
    now = time.time()
    if _cache and (now - _cache.get("fetched_at", 0)) < _CACHE_TTL:
        logger.info(f"[exchange_rate] Using cached rate: {_cache['rate']} NGN/USD")
        return _cache["rate"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://open.er-api.com/v6/latest/USD")
            resp.raise_for_status()
            data = resp.json()
            rate = float(data["rates"]["NGN"])
            _cache["rate"] = rate
            _cache["fetched_at"] = now
            logger.info(f"[exchange_rate] Fetched live rate: {rate} NGN/USD")
            return rate
    except Exception as exc:
        fallback = _cache.get("rate", 1600.0)
        logger.warning(f"[exchange_rate] Failed to fetch rate ({exc}); using {fallback} NGN/USD")
        return fallback
