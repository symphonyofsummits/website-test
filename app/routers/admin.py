"""Admin endpoints — trip/batch CRUD, lead board, dashboards."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Batch, Booking, Lead, Payment, Trip, User
from app.models.enums import BookingStatus, LeadStatus, PaymentStatus
from app.schemas.schemas import (
    BatchCreate, BatchOut, LeadOut, TripCreate, TripDetailOut,
)
from app.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------------- TRIPS ----------------
@router.post("/trips", response_model=TripDetailOut, status_code=201)
async def create_trip(
    payload: TripCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(Trip).where(Trip.slug == payload.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Slug already in use")

    trip = Trip(**payload.model_dump(), created_by=admin.id)
    db.add(trip)
    await db.flush()
    return trip


@router.patch("/trips/{trip_id}", response_model=TripDetailOut)
async def update_trip(
    trip_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    trip = (await db.execute(select(Trip).where(Trip.id == trip_id))).scalar_one_or_none()
    if not trip:
        raise HTTPException(404, "Trip not found")
    for k, v in payload.items():
        if hasattr(trip, k):
            setattr(trip, k, v)
    return trip


@router.post("/trips/{trip_id}/publish", response_model=TripDetailOut)
async def publish_trip(trip_id: UUID, db: AsyncSession = Depends(get_db)):
    trip = (await db.execute(select(Trip).where(Trip.id == trip_id))).scalar_one_or_none()
    if not trip:
        raise HTTPException(404, "Trip not found")
    trip.is_published = True
    from datetime import datetime, timezone
    trip.published_at = datetime.now(timezone.utc)
    return trip


# ---------------- BATCHES ----------------
@router.post("/batches", response_model=BatchOut, status_code=201)
async def create_batch(payload: BatchCreate, db: AsyncSession = Depends(get_db)):
    batch = Batch(**payload.model_dump())
    db.add(batch)
    await db.flush()
    return BatchOut(
        id=batch.id, trip_id=batch.trip_id, batch_code=batch.batch_code,
        start_date=batch.start_date, end_date=batch.end_date,
        total_seats=batch.total_seats, booked_seats=batch.booked_seats,
        reserved_seats=batch.reserved_seats, price_override=batch.price_override,
        status=batch.status, seats_available=batch.seats_available,
    )


# ---------------- LEADS ----------------
@router.get("/leads", response_model=List[LeadOut])
async def list_leads(
    status: Optional[LeadStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Lead).order_by(Lead.created_at.desc())
    if status:
        stmt = stmt.where(Lead.status == status.value)
    return (await db.execute(stmt.limit(200))).scalars().all()


@router.patch("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: UUID,
    status: Optional[LeadStatus] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    if status:
        lead.status = status.value
    if notes is not None:
        lead.notes = notes
    return lead


# ---------------- DASHBOARD ----------------
@router.get("/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    bookings_total = (await db.execute(select(func.count(Booking.id)))).scalar()
    bookings_confirmed = (await db.execute(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.CONFIRMED.value)
    )).scalar()
    revenue = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.status == PaymentStatus.SUCCESS.value)
    )).scalar()
    leads_new = (await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.NEW.value)
    )).scalar()
    pending_payments = (await db.execute(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatus.PROCESSING.value)
    )).scalar()

    return {
        "bookings_total": bookings_total,
        "bookings_confirmed": bookings_confirmed,
        "revenue_inr": float(revenue or 0),
        "leads_new": leads_new,
        "pending_payment_verifications": pending_payments,
    }
