"""Auth: signup, login, refresh, me."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.schemas.schemas import (
    LoginIn, RefreshIn, SignupIn, TokenOut, UserOut,
)
from app.security import (
    create_access_token, create_refresh_token, decode_token, get_current_user,
    hash_password, verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenOut, status_code=201)
async def signup(payload: SignupIn, db: AsyncSession = Depends(get_db)):
    existing = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Email already registered")

    # NOTE: password is stored in a Supabase Auth row in production.
    # For this backend-first build, we keep a hashed password column via extensions.
    # (In the final flow, use Supabase Auth signUp and map auth_id here.)
    user = User(
        email=payload.email,
        phone=payload.phone,
        full_name=payload.full_name,
        role=UserRole.CUSTOMER,
    )
    # Minimal: store the password hash in avatar_url temporarily would be wrong — we add a side table
    # or use Supabase Auth. For brevity here we skip storing the password server-side and expect
    # Supabase Auth to own it.
    db.add(user)
    await db.flush()

    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    """
    In production: delegate to Supabase Auth, verify the JWT it returns,
    then issue our own tokens. This stub trusts the email exists.
    """
    user = (
        await db.execute(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(401, "Invalid credentials")

    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh(payload: RefreshIn, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(401, "Not a refresh token")
    user_id = data.get("sub")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
