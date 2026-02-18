"""
GB Guide — Authentication Routes

POST /api/auth/register  — Create a new user account
POST /api/auth/login     — Authenticate and receive a JWT
GET  /api/auth/me        — Return the current user's profile (protected)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_session
from app.models import User
from app.schemas.user import Token, UserCreate, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ═══════════════════════════════════════════════════════════════════
# REGISTER
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(
    user_in: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Register a new user.

    - Validates the input via `UserCreate` schema.
    - Checks for duplicate emails.
    - Hashes the password before storing.
    - Returns the created user (without password_hash).
    """
    # ── Check for duplicate email ───────────────────────────────
    stmt = select(User).where(User.email == user_in.email)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # ── Create and persist ──────────────────────────────────────
    db_user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        city=user_in.city,
        phone_number=user_in.phone_number,
        role=user_in.role,
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


# ═══════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT access token",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Authenticate with email + password.

    Uses `OAuth2PasswordRequestForm` so Swagger UI's "Authorize" button
    works out of the box. The `username` field accepts the user's email.

    Returns a JWT access token on success.
    """
    # ── Find user by email ──────────────────────────────────────
    stmt = select(User).where(User.email == form_data.username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    # ── Verify credentials ──────────────────────────────────────
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Issue token ─────────────────────────────────────────────
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token)


# ═══════════════════════════════════════════════════════════════════
# CURRENT USER PROFILE (PROTECTED)
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user's profile",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    **Protected endpoint** — requires a valid JWT in the `Authorization` header.

    Returns the full profile of the currently authenticated user.
    Uses the `get_current_user` dependency which:
    1. Extracts the Bearer token
    2. Decodes the JWT
    3. Fetches the user from the database
    """
    return current_user
