"""
GB Guide — Hotel & Room Routes

POST   /api/hotels                     — Create a hotel (HOTEL_OWNER / ADMIN)
GET    /api/hotels                     — List all hotels (public)
GET    /api/hotels/my/hotels           — Get hotels owned by current user (protected)
GET    /api/hotels/{hotel_id}          — Get a hotel with rooms (public)
POST   /api/hotels/{hotel_id}/rooms    — Add a room to a hotel (owner only)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.security import RoleChecker, get_current_user
from app.database import get_session
from app.models import Hotel, Room, User, UserRole
from app.schemas.hotel import (
    HotelCreate,
    HotelListResponse,
    HotelResponse,
    RoomCreate,
    RoomResponse,
)

router = APIRouter(prefix="/api/hotels", tags=["Hotels"])

# ── Reusable RBAC dependency ────────────────────────────────────
require_hotel_role = RoleChecker([UserRole.HOTEL_OWNER, UserRole.ADMIN])


# ═══════════════════════════════════════════════════════════════════
# CREATE HOTEL
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=HotelListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new hotel",
)
async def create_hotel(
    hotel_in: HotelCreate,
    current_user: Annotated[User, Depends(require_hotel_role)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    **Protected** — Only `hotel_owner` and `admin` roles.

    Creates a new hotel. The `owner_id` is automatically set to
    the authenticated user's ID.
    """
    db_hotel = Hotel(
        owner_id=current_user.id,
        name=hotel_in.name,
        location=hotel_in.location,
        city=hotel_in.city,
        description=hotel_in.description,
        images=hotel_in.images,
    )
    session.add(db_hotel)
    await session.commit()
    await session.refresh(db_hotel)

    return db_hotel


# ═══════════════════════════════════════════════════════════════════
# LIST ALL HOTELS (PUBLIC)
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=list[HotelListResponse],
    summary="List all hotels",
)
async def list_hotels(
    session: Annotated[AsyncSession, Depends(get_session)],
    city: str | None = None,
):
    """
    **Public** — Returns all hotels. Optionally filter by `city`.

    Uses `HotelListResponse` (no rooms) to keep the payload light.
    """
    stmt = select(Hotel).order_by(Hotel.created_at.desc())
    if city:
        stmt = stmt.where(Hotel.city.ilike(f"%{city}%"))

    result = await session.execute(stmt)
    hotels = result.scalars().all()
    return hotels


# ═══════════════════════════════════════════════════════════════════
# GET MY HOTELS (PROTECTED — for dashboard)
# ═══════════════════════════════════════════════════════════════════
# ⚠ MUST be defined BEFORE /{hotel_id} so FastAPI doesn't try
#   to parse "my" as an integer.

@router.get(
    "/my/hotels",
    response_model=list[HotelResponse],
    summary="Get hotels owned by the current user",
)
async def get_my_hotels(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    **Protected** — Returns all hotels owned by the authenticated user,
    including their rooms. Used by the hotel owner dashboard.
    """
    stmt = (
        select(Hotel)
        .where(Hotel.owner_id == current_user.id)
        .options(selectinload(Hotel.rooms))  # type: ignore[arg-type]
        .order_by(Hotel.created_at.desc())
    )
    result = await session.execute(stmt)
    hotels = result.scalars().all()
    return hotels


# ═══════════════════════════════════════════════════════════════════
# GET HOTEL DETAIL (PUBLIC)
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/{hotel_id}",
    response_model=HotelResponse,
    summary="Get a hotel and its rooms",
)
async def get_hotel(
    hotel_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    **Public** — Returns a single hotel with all its rooms.

    Uses `selectinload` to eagerly load rooms in a single query
    (avoids N+1).
    """
    stmt = (
        select(Hotel)
        .where(Hotel.id == hotel_id)
        .options(selectinload(Hotel.rooms))  # type: ignore[arg-type]
    )
    result = await session.execute(stmt)
    hotel = result.scalar_one_or_none()

    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel with id {hotel_id} not found.",
        )

    return hotel


# ═══════════════════════════════════════════════════════════════════
# ADD ROOM TO HOTEL
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/{hotel_id}/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a room to a hotel",
)
async def add_room(
    hotel_id: int,
    room_in: RoomCreate,
    current_user: Annotated[User, Depends(require_hotel_role)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    **Protected** — Only the hotel's owner (or admin) can add rooms.

    Critical ownership check: verifies `current_user.id` matches
    the hotel's `owner_id` before allowing the operation.
    Admins bypass this check.
    """
    # ── Fetch hotel ─────────────────────────────────────────────
    hotel = await session.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel with id {hotel_id} not found.",
        )

    # ── Ownership check (admins can bypass) ─────────────────────
    if (
        current_user.role != UserRole.ADMIN
        and hotel.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add rooms to your own hotel.",
        )

    # ── Create room ─────────────────────────────────────────────
    db_room = Room(
        hotel_id=hotel_id,
        room_type=room_in.room_type,
        price_per_night=room_in.price_per_night,
        capacity=room_in.capacity,
        is_available=room_in.is_available,
    )
    session.add(db_room)
    await session.commit()
    await session.refresh(db_room)

    return db_room
