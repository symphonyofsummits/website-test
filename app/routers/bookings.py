"""Booking endpoints."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Booking, User
from app.models.enums import LeadSource
from app.schemas.schemas import BookingCreate, BookingOut
from app.security import get_current_user
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=201)
async def create_booking(
    payload: BookingCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    booking = await booking_service.create_booking(
        db=db, user=user, payload=payload, client_ip=client_ip,
        source=LeadSource.WEBSITE_FORM,
    )
    # Re-fetch with travellers eager-loaded for response
    stmt = select(Booking).options(selectinload(Booking.travellers)).where(Booking.id == booking.id)
    return (await db.execute(stmt)).scalar_one()


@router.get("", response_model=List[BookingOut])
async def my_bookings(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Booking)
        .options(selectinload(Booking.travellers))
        .where(Booking.user_id == user.id)
        .order_by(Booking.created_at.desc())
    )
    return (await db.execute(stmt)).scalars().all()


@router.get("/{booking_id}", response_model=BookingOut)
async def booking_detail(
    booking_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Booking)
        .options(selectinload(Booking.travellers))
        .where(Booking.id == booking_id, Booking.user_id == user.id)
    )
    booking = (await db.execute(stmt)).scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: UUID,
    reason: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = (
        await db.execute(select(Booking).where(Booking.id == booking_id, Booking.user_id == user.id))
    ).scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")
    await booking_service.cancel_booking(db, booking, reason)
    return booking
