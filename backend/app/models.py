"""
GB Guide — Database Models

All SQLModel table definitions live here.
Import this module in alembic/env.py so Alembic can detect tables.

Architecture:
    User ──┬── Hotel ── Room
           ├── Car
           └── GuideProfile
"""

import enum
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR


# ═══════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════

class UserRole(str, enum.Enum):
    """Roles that determine what a user can do on the platform."""
    CUSTOMER = "customer"
    ADMIN = "admin"
    HOTEL_OWNER = "hotel_owner"
    CAR_RENTAL = "car_rental"
    GUIDE = "guide"


class VerificationStatus(str, enum.Enum):
    """Approval status for provider-type entities (Car, GuideProfile)."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


# ═══════════════════════════════════════════════════════════════════
# USER
# ═══════════════════════════════════════════════════════════════════

class User(SQLModel, table=True):
    """
    Central user table — every person on the platform has exactly one row.
    The `role` field determines which child relationships are meaningful.
    """
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Login email — must be unique.",
    )
    password_hash: str = Field(
        max_length=255,
        description="Bcrypt / Argon2 hash — never store plaintext.",
    )
    full_name: str = Field(max_length=150)
    city: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    role: UserRole = Field(
        default=UserRole.CUSTOMER,
        sa_column=Column(
            SAEnum(
                UserRole,
                name="userrole",
                create_constraint=True,
                values_callable=lambda e: [member.value for member in e],
            ),
            nullable=False,
            server_default=UserRole.CUSTOMER.value,
        ),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ── Relationships ───────────────────────────────────────────
    hotels: List["Hotel"] = Relationship(back_populates="owner")
    cars: List["Car"] = Relationship(back_populates="owner")
    guide_profile: Optional["GuideProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False},
    )


# ═══════════════════════════════════════════════════════════════════
# HOTEL  +  ROOM
# ═══════════════════════════════════════════════════════════════════

class Hotel(SQLModel, table=True):
    """
    A hotel listed by a HOTEL_OWNER user.
    Images are stored as a PostgreSQL text[] array of URLs.
    """
    __tablename__ = "hotels"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=200)
    location: str = Field(
        max_length=300,
        description="Full address or coordinates.",
    )
    city: str = Field(
        max_length=100,
        description="GB city — e.g. Gilgit, Skardu, Hunza.",
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    images: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(VARCHAR), nullable=True),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ── Relationships ───────────────────────────────────────────
    owner: "User" = Relationship(back_populates="hotels")
    rooms: List["Room"] = Relationship(back_populates="hotel")


class Room(SQLModel, table=True):
    """A room type within a hotel — e.g. Deluxe, Standard."""
    __tablename__ = "rooms"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    room_type: str = Field(
        max_length=100,
        description="E.g. Deluxe, Standard, Suite.",
    )
    price_per_night: float = Field(description="Price in PKR.")
    capacity: int = Field(default=2, description="Max guests.")
    is_available: bool = Field(default=True)

    # ── Relationships ───────────────────────────────────────────
    hotel: "Hotel" = Relationship(back_populates="rooms")


# ═══════════════════════════════════════════════════════════════════
# CAR
# ═══════════════════════════════════════════════════════════════════

class Car(SQLModel, table=True):
    """
    A car listed by a CAR_RENTAL user.
    Requires admin verification before becoming visible.
    """
    __tablename__ = "cars"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    make: str = Field(max_length=100, description="E.g. Toyota, Suzuki.")
    model: str = Field(max_length=100, description="E.g. Corolla, Bolan.")
    license_plate: str = Field(max_length=20, unique=True)
    with_driver: bool = Field(
        default=True,
        description="True = comes with driver, False = self-drive.",
    )
    status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        sa_column=Column(
            SAEnum(
                VerificationStatus,
                name="verificationstatus",
                create_constraint=True,
                values_callable=lambda e: [member.value for member in e],
            ),
            nullable=False,
            server_default=VerificationStatus.PENDING.value,
        ),
    )
    driver_license_image: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL to uploaded driver license image.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ── Relationships ───────────────────────────────────────────
    owner: "User" = Relationship(back_populates="cars")


# ═══════════════════════════════════════════════════════════════════
# GUIDE PROFILE
# ═══════════════════════════════════════════════════════════════════

class GuideProfile(SQLModel, table=True):
    """
    Extended profile for a GUIDE user.
    One-to-one with User — enforced via unique constraint on user_id.
    """
    __tablename__ = "guide_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        unique=True,
        index=True,
    )
    bio: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    daily_rate: float = Field(description="Daily rate in PKR.")
    languages: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(VARCHAR), nullable=True),
        description="E.g. ['Urdu', 'English', 'Brushaski'].",
    )
    status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        sa_column=Column(
            SAEnum(
                VerificationStatus,
                name="verificationstatus",
                create_constraint=True,
                create_type=False,       # re-use the type created by Car
                values_callable=lambda e: [member.value for member in e],
            ),
            nullable=False,
            server_default=VerificationStatus.PENDING.value,
        ),
    )
    cnic_image: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL to uploaded CNIC image for verification.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ── Relationships ───────────────────────────────────────────
    user: "User" = Relationship(back_populates="guide_profile")
