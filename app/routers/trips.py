"""Public catalog endpoints — trips, batches, filters."""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Batch, Trip
from app.models.enums import BatchStatus, Difficulty, TripCategory, TripScope
from app.schemas.schemas import BatchOut, TripDetailOut, TripListOut

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=List[TripListOut])
async def list_trips(
    db: AsyncSession = Depends(get_db),
    category: Optional[TripCategory] = None,
    scope: Optional[TripScope] = None,
    difficulty: Optional[Difficulty] = None,
    region: Optional[str] = None,
    search: Optional[str] = None,
    featured: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    stmt = select(Trip).where(Trip.is_published.is_(True))
    if category:
        stmt = stmt.where(Trip.category == category.value)
    if scope:
        stmt = stmt.where(Trip.scope == scope.value)
    if difficulty:
        stmt = stmt.where(Trip.difficulty == difficulty.value)
    if region:
        stmt = stmt.where(Trip.region.ilike(f"%{region}%"))
    if featured:
        stmt = stmt.where(Trip.is_featured.is_(True))
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(or_(
            func.lower(Trip.title).like(pattern),
            func.lower(Trip.region).like(pattern),
        ))

    stmt = stmt.order_by(Trip.is_featured.desc(), Trip.created_at.desc())
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    return rows


@router.get("/{slug}", response_model=TripDetailOut)
async def trip_detail(slug: str, db: AsyncSession = Depends(get_db)):
    trip = (
        await db.execute(select(Trip).where(Trip.slug == slug, Trip.is_published.is_(True)))
    ).scalar_one_or_none()
    if not trip:
        raise HTTPException(404, "Trip not found")
    return trip


@router.get("/{slug}/batches", response_model=List[BatchOut])
async def trip_batches(
    slug: str,
    db: AsyncSession = Depends(get_db),
    from_date: Optional[date] = Query(None),
    include_sold_out: bool = False,
):
    trip = (await db.execute(select(Trip).where(Trip.slug == slug))).scalar_one_or_none()
    if not trip:
        raise HTTPException(404, "Trip not found")

    stmt = select(Batch).where(Batch.trip_id == trip.id)
    if from_date:
        stmt = stmt.where(Batch.start_date >= from_date)
    else:
        stmt = stmt.where(Batch.start_date >= func.current_date())

    if not include_sold_out:
        stmt = stmt.where(Batch.status.notin_(["cancelled", "completed"]))

    stmt = stmt.order_by(Batch.start_date)
    rows = (await db.execute(stmt)).scalars().all()

    return [BatchOut(
        id=b.id, trip_id=b.trip_id, batch_code=b.batch_code,
        start_date=b.start_date, end_date=b.end_date,
        total_seats=b.total_seats, booked_seats=b.booked_seats,
        reserved_seats=b.reserved_seats, price_override=b.price_override,
        status=b.status, seats_available=b.seats_available,
    ) for b in rows]


@router.get("/by/upcoming", response_model=List[BatchOut])
async def all_upcoming_batches(
    db: AsyncSession = Depends(get_db),
    category: Optional[TripCategory] = None,
    limit: int = Query(30, ge=1, le=100),
):
    """TrekUpIndia-style flat feed: upcoming batches across all trips."""
    stmt = (
        select(Batch, Trip)
        .join(Trip, Trip.id == Batch.trip_id)
        .where(Trip.is_published.is_(True))
        .where(Batch.start_date >= func.current_date())
        .where(Batch.status.notin_(["cancelled", "sold_out", "completed"]))
    )
    if category:
        stmt = stmt.where(Trip.category == category.value)
    stmt = stmt.order_by(Batch.start_date).limit(limit)

    rows = (await db.execute(stmt)).all()
    return [BatchOut(
        id=b.id, trip_id=b.trip_id, batch_code=b.batch_code,
        start_date=b.start_date, end_date=b.end_date,
        total_seats=b.total_seats, booked_seats=b.booked_seats,
        reserved_seats=b.reserved_seats, price_override=b.price_override,
        status=b.status, seats_available=b.seats_available,
    ) for b, _ in rows]
