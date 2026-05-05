from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from typing import Tuple
import math

_geolocator = Nominatim(user_agent="baros_app")


def calculate_distance_km(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Straight-line distance between two points in kilometers.
    Uses geodesic (WGS‑84 ellipsoid) for accuracy.
    """
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


def is_within_radius(
    center_lat: float, center_lon: float,
    point_lat: float, point_lon: float,
    radius_km: float
) -> bool:
    """
    Returns True if the point is within the radius of the center.
    """
    return calculate_distance_km(center_lat, center_lon, point_lat, point_lon) <= radius_km


def bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """
    Approximate bounding box for a given point and radius.
    Returns (min_lat, min_lon, max_lat, max_lon).
    """
    lat_delta = radius_km / 111.32  # 1 degree ≈ 111.32 km
    lon_delta = radius_km / (111.32 * math.cos(math.radians(lat)))
    return (lat - lat_delta, lon - lon_delta, lat + lat_delta, lon + lon_delta)