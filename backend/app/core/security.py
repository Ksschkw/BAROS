from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, APIKeyCookie
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple Bearer token scheme for Swagger UI (shows just a token input)
bearer_scheme = HTTPBearer(auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")

# Cookie scheme to read token from "access_token" cookie
cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_token_from_request(request: Request) -> str:
    """Extract JWT token from cookie first, then from Authorization header."""
    # Try cookie first (for real frontend)
    cookie_token = await cookie_scheme(request)
    if cookie_token:
        return cookie_token

    # Fallback to Bearer header (for Swagger UI testing)
    bearer_credentials = await bearer_scheme(request)
    if bearer_credentials:
        return bearer_credentials.credentials

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )