import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.dependencies import get_db, get_current_user
from ....core.security import create_access_token, verify_password, decode_access_token
from ....core.config import settings
from ....crud.user import (
    get_user_by_email,
    get_user_by_google_id,
    create_user,
    create_user_from_google,
)
from ....schemas.user import UserCreate, UserLogin, UserGoogleAuth, UserOut
from ....models.user import User

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = await create_user(db, user_in)
    return user


@router.post("/login")
async def login(login_in: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, login_in.email)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(user.id)})

    # Set httpOnly secure cookie for the frontend
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.SECURE_COOKIES,   # I will set to True in production with HTTPS
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"access_token": token, "token_type": "bearer"}


@router.post("/google")
async def google_auth(auth_data: UserGoogleAuth, response: Response, db: AsyncSession = Depends(get_db)):
    from google.oauth2 import id_token
    from google.auth.transport import requests

    try:
        idinfo = id_token.verify_oauth2_token(
            auth_data.token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        print(f"Google token verification failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Google token: {str(e)}")

    google_id = idinfo["sub"]
    email = idinfo.get("email")
    name = idinfo.get("name", email)

    user = await get_user_by_google_id(db, google_id)
    if not user:
        user = await get_user_by_email(db, email)
        if user:
            user.google_id = google_id
            await db.commit()
        else:
            user = await create_user_from_google(db, email, google_id, name)

    token = create_access_token(data={"sub": str(user.id)})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.SECURE_COOKIES,   # True in production with HTTPS
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"access_token": token, "token_type": "bearer"}


# @router.get("/me", response_model=UserOut)
# async def me(current_user: User = Depends(get_current_user)):
#     return current_user
from fastapi import Security
from ....core.security import bearer_scheme

@router.get("/me", response_model=UserOut)
async def me(
    current_user: User = Depends(get_current_user),
    _bearer: str = Security(bearer_scheme),   # Only to trigger OpenAPI security
):
    return current_user

@router.post("/link-google")
async def link_google(
    auth_data: UserGoogleAuth,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import requests as req
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests

    # Create a session that skips SSL verification (DEVELOPMENT ONLY)
    session = req.Session()
    session.verify = False
    transport = google_requests.Request(session=session)

    try:
        idinfo = google_id_token.verify_oauth2_token(
            auth_data.token,
            transport,
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google verification failed: {e}")

    google_id = idinfo["sub"]
    google_email = idinfo.get("email")
    google_name = idinfo.get("name")

    # Check if this Google account is already linked to another user
    existing = await get_user_by_google_id(db, google_id)
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=409, detail="Google account already linked to another user")

    # Link Google ID
    current_user.google_id = google_id

    # Update display name from Google (always safe)
    if google_name:
        current_user.display_name = google_name

    # Update email only if it's different and not already taken by another user
    if google_email and google_email != current_user.email:
        email_owner = await get_user_by_email(db, google_email)
        if email_owner and email_owner.id != current_user.id:
            raise HTTPException(status_code=409, detail="Google email is already used by another account")
        current_user.email = google_email

    await db.commit()
    return {"message": "Google account linked"}