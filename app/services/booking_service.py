"""
Core booking engine — the heart of the app.
Uses the DB's reserve_seats() function for ACID seat inventory.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Batch, Booking, Coupon, Traveller, Trip, User
from app.models.enums import BookingStatus, LeadSource
from app.schemas.schemas import BookingCreate, TravellerIn

logger = logging.getLogger(__name__)


async def _reserve_seats_atomic(db: AsyncSession, batch_id: UUID, seats: int) -> bool:
    """Call Postgres reserve_seats() which does SELECT ... FOR UPDATE."""
    result = await db.execute(
        text("SELECT reserve_seats(:bid, :seats)"),
        {"bid": str(batch_id), "seats": seats},
    )
    return bool(result.scalar())


async def _release_seats_atomic(db: AsyncSession, batch_id: UUID, seats: int) -> None:
    await db.execute(
        text("SELECT release_seats(:bid, :seats)"),
        {"bid": str(batch_id), "seats": seats},
    )


async def _confirm_seats_atomic(db: AsyncSession, batch_id: UUID, seats: int) -> None:
    await db.execute(
        text("SELECT confirm_seats(:bid, :seats)"),
        {"bid": str(batch_id), "seats": seats},
    )


async def _apply_coupon(
    db: AsyncSession, coupon_code: str, base_amount: Decimal, user_id: UUID
) -> tuple[Optional[Coupon], Decimal]:
    """Returns (coupon_or_none, discount_amount). Raises if invalid."""
    coupon = (
        await db.execute(select(Coupon).where(Coupon.code == coupon_code.upper(), Coupon.is_active.is_(True)))
    ).scalar_one_or_none()
    if not coupon:
        raise HTTPException(400, f"Coupon '{coupon_code}' is invalid")
    now = datetime.now(timezone.utc)
    if coupon.valid_from and now < coupon.valid_from:
        raise HTTPException(400, "Coupon not yet active")
    if coupon.valid_until and now > coupon.valid_until:
        raise HTTPException(400, "Coupon has expired")
    if coupon.min_order_value and base_amount < coupon.min_order_value:
        raise HTTPException(400, f"Minimum order ₹{coupon.min_order_value} required for this coupon")
    if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        raise HTTPException(400, "Coupon usage limit reached")

    if coupon.discount_type == "percent":
        discount = (base_amount * coupon.discount_value / Decimal("100")).quantize(Decimal("0.01"))
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
    else:
        discount = Decimal(coupon.discount_value)

    return coupon, min(discount, base_amount)


async def create_booking(
    db: AsyncSession,
    user: User,
    payload: BookingCreate,
    client_ip: Optional[str] = None,
    source: LeadSource = LeadSource.WEBSITE_FORM,
) -> Booking:
    """
    Atomic booking creation:
    1. Lock batch row & reserve seats (SELECT FOR UPDATE inside DB function)
    2. Price out base + discount + GST
    3. Create booking + travellers
    4. Return — payment is a separate step
    """
    seats = len(payload.travellers)

    # Fetch batch + trip (locked read is in reserve_seats; this is just for display + pricing)
    batch = (
        await db.execute(select(Batch).where(Batch.id == payload.batch_id))
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(404, "Batch not found")

    trip = (await db.execute(select(Trip).where(Trip.id == batch.trip_id))).scalar_one()

    # Reserve seats atomically
    reserved = await _reserve_seats_atomic(db, batch.id, seats)
    if not reserved:
        raise HTTPException(409, "Not enough seats available in this batch")

    # Pricing
    unit_price = Decimal(batch.price_override or trip.base_price)
    base_amount = (unit_price * seats).quantize(Decimal("0.01"))

    discount_amount = Decimal("0")
    coupon_id = None
    if payload.coupon_code:
        coupon, discount_amount = await _apply_coupon(db, payload.coupon_code, base_amount, user.id)
        coupon_id = coupon.id
        coupon.used_count += 1

    taxable = base_amount - discount_amount
    gst_amount = (taxable * trip.gst_pct / Decimal("100")).quantize(Decimal("0.01"))
    total_amount = (taxable + gst_amount).quantize(Decimal("0.01"))

    booking = Booking(
        user_id=user.id,
        trip_id=trip.id,
        batch_id=batch.id,
        travellers_count=seats,
        base_amount=base_amount,
        discount_amount=discount_amount,
        gst_amount=gst_amount,
        total_amount=total_amount,
        advance_paid=Decimal("0"),
        balance_due=total_amount,
        status=BookingStatus.PENDING,
        coupon_id=coupon_id,
        special_requests=payload.special_requests,
        pickup_point=payload.pickup_point,
        booked_from_ip=client_ip,
        booked_from_source=source,
    )
    db.add(booking)
    await db.flush()  # get booking.id

    for i, tv in enumerate(payload.travellers):
        db.add(Traveller(
            booking_id=booking.id,
            is_lead=(i == 0) or tv.is_lead,
            full_name=tv.full_name,
            age=tv.age,
            gender=tv.gender,
            phone=tv.phone,
            email=tv.email,
            id_proof_type=tv.id_proof_type,
            id_proof_number=tv.id_proof_number,
            medical_conditions=tv.medical_conditions,
            blood_group=tv.blood_group,
            emergency_contact_name=tv.emergency_contact_name,
            emergency_contact_phone=tv.emergency_contact_phone,
        ))

    await db.flush()
    return booking


async def confirm_booking(db: AsyncSession, booking: Booking, paid_amount: Decimal) -> Booking:
    """Called after a successful payment — moves reserved → booked, confirms the booking."""
    booking.advance_paid = (booking.advance_paid or Decimal("0")) + paid_amount
    booking.balance_due = max(booking.total_amount - booking.advance_paid, Decimal("0"))

    # Only flip to CONFIRMED when at least the advance is covered
    trip = (await db.execute(select(Trip).where(Trip.id == booking.trip_id))).scalar_one()
    if booking.advance_paid >= trip.advance_amount and booking.status == BookingStatus.PENDING:
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.now(timezone.utc)
        await _confirm_seats_atomic(db, booking.batch_id, booking.travellers_count)
    return booking


async def cancel_booking(db: AsyncSession, booking: Booking, reason: str = "") -> Booking:
    """Release seats and mark booking cancelled. Refund is a separate flow."""
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(400, "Booking already cancelled")
    if booking.status == BookingStatus.PENDING:
        await _release_seats_atomic(db, booking.batch_id, booking.travellers_count)
    else:
        # Was confirmed → decrement booked_seats
        batch = (await db.execute(select(Batch).where(Batch.id == booking.batch_id))).scalar_one()
        batch.booked_seats = max(batch.booked_seats - booking.travellers_count, 0)

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    booking.cancellation_reason = reason
    return booking
