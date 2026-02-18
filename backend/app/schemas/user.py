"""
GB Guide — User Pydantic Schemas

Separate from SQLModel table models — these control what the API
accepts (input) and returns (output). Never expose password_hash.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole


# ═══════════════════════════════════════════════════════════════════
# INPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)
    city: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    role: UserRole = UserRole.CUSTOMER


# ═══════════════════════════════════════════════════════════════════
# OUTPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    """
    Schema returned to the client.
    Deliberately excludes password_hash.
    """
    id: int
    email: str
    full_name: str
    city: str | None = None
    phone_number: str | None = None
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# TOKEN SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class Token(BaseModel):
    """Returned on successful login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Internal — decoded from the JWT payload."""
    user_id: int | None = None
