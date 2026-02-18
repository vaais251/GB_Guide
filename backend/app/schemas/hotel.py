"""
GB Guide — Hotel & Room Pydantic Schemas

Input/output schemas for the Hotel and Room endpoints.
HotelResponse nests RoomResponse so a single GET returns
the hotel + all its rooms.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# ROOM SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class RoomCreate(BaseModel):
    """Schema for creating a room inside a hotel."""
    room_type: str = Field(
        min_length=1,
        max_length=100,
        examples=["Deluxe", "Standard", "Suite"],
    )
    price_per_night: float = Field(
        gt=0,
        description="Price per night in PKR.",
        examples=[5000.0],
    )
    capacity: int = Field(
        default=2,
        ge=1,
        le=20,
        description="Maximum number of guests.",
    )
    is_available: bool = Field(default=True)


class RoomResponse(BaseModel):
    """Room data returned to the client."""
    id: int
    hotel_id: int
    room_type: str
    price_per_night: float
    capacity: int
    is_available: bool

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# HOTEL SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class HotelCreate(BaseModel):
    """Schema for creating a new hotel."""
    name: str = Field(
        min_length=1,
        max_length=200,
        examples=["Serena Hotel Gilgit"],
    )
    location: str = Field(
        min_length=1,
        max_length=300,
        description="Full address or coordinates.",
        examples=["Jutial, Gilgit 15100"],
    )
    city: str = Field(
        min_length=1,
        max_length=100,
        description="City in Gilgit-Baltistan.",
        examples=["Gilgit"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        examples=["A premium hotel with mountain views and modern amenities."],
    )
    images: Optional[list[str]] = Field(
        default=None,
        description="List of image URLs.",
    )


class HotelResponse(BaseModel):
    """
    Hotel data returned to the client.
    Includes nested rooms for detail views.
    """
    id: int
    owner_id: int
    name: str
    location: str
    city: str
    description: Optional[str] = None
    images: Optional[list[str]] = None
    created_at: datetime
    rooms: list[RoomResponse] = []

    model_config = {"from_attributes": True}


class HotelListResponse(BaseModel):
    """
    Lightweight hotel data for list views (no rooms).
    Avoids N+1 queries on the listing page.
    """
    id: int
    owner_id: int
    name: str
    location: str
    city: str
    description: Optional[str] = None
    images: Optional[list[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
