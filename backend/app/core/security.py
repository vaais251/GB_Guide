"""
GB Guide — Security Utilities

Password hashing, JWT creation/verification, and the
`get_current_user` FastAPI dependency.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session
from app.models import User, UserRole

# ═══════════════════════════════════════════════════════════════════
# PASSWORD HASHING
# ═══════════════════════════════════════════════════════════════════

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════════════════════════════
# JWT TOKEN
# ═══════════════════════════════════════════════════════════════════

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload dict — must include a "sub" key (user identifier).
        expires_delta: Custom expiry; defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ═══════════════════════════════════════════════════════════════════
# FASTAPI DEPENDENCY — get_current_user
# ═══════════════════════════════════════════════════════════════════

# This makes the "Authorize" button appear in Swagger UI.
# The tokenUrl must match the login endpoint path.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Reusable HTTP 401 exception
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    FastAPI dependency: decode the JWT, look up the user, and return
    the User ORM object. Raises 401 if anything fails.

    Usage in a route:
        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
            ...
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch user from DB
    user = await session.get(User, int(user_id))
    if user is None:
        raise credentials_exception

    return user


# ═══════════════════════════════════════════════════════════════════
# ROLE-BASED ACCESS CONTROL (RBAC)
# ═══════════════════════════════════════════════════════════════════

class RoleChecker:
    """
    FastAPI dependency that enforces role-based access.

    Usage::

        require_hotel_owner = RoleChecker([UserRole.HOTEL_OWNER, UserRole.ADMIN])

        @router.post("/hotels")
        async def create_hotel(
            current_user: Annotated[User, Depends(require_hotel_owner)],
        ):
            ...

    Raises HTTP 403 Forbidden if the user's role is not in
    the allowed list.
    """

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted. "
                       f"Required: {[r.value for r in self.allowed_roles]}.",
            )
        return current_user
