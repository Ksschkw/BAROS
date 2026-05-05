import httpx
from urllib.parse import urlencode
from ..core.config import settings

STADIA_API_KEY = settings.STADIA_MAPS_API_KEY


async def geocode(query: str) -> dict:
    """
    Forward geocoding: converts an address to coordinates.
    """
    url = "https://api-eu.stadiamaps.com/geocoding/v1/search"
    params = {"text": query, "api_key": STADIA_API_KEY}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Reverse geocoding: converts coordinates to an address.
    """
    url = "https://api-eu.stadiamaps.com/geocoding/v1/reverse"
    params = {"point.lat": lat, "point.lon": lon, "api_key": STADIA_API_KEY}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def get_directions(
    start_lat: float, start_lon: float,
    end_lat: float, end_lon: float
) -> dict:
    """
    Calculates a route between two points.
    """
    url = f"https://api-eu.stadiamaps.com/directions/v2/route"
    params = {
        "api_key": STADIA_API_KEY,
        "origin": f"{start_lat},{start_lon}",
        "destination": f"{end_lat},{end_lon}",
        "mode": "drive",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()