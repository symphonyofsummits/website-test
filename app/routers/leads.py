"""Lead capture — the quote form and WhatsApp notification pipeline."""
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Lead, Trip
from app.schemas.schemas import LeadCreate, LeadOut, MessageOut
from app.services import email_service, whatsapp_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
async def submit_lead(
    payload: LeadCreate,
    background: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Open endpoint — called by the website quote form.
    Writes the lead and fires WhatsApp alerts to admins + ack email to user in background.
    """
    trip_title = "General Enquiry"
    if payload.interested_trip_id:
        trip = (
            await db.execute(select(Trip).where(Trip.id == payload.interested_trip_id))
        ).scalar_one_or_none()
        if trip:
            trip_title = trip.title

    lead = Lead(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        city=payload.city,
        interested_trip_id=payload.interested_trip_id,
        travellers_count=payload.travellers_count,
        preferred_date=payload.preferred_date,
        budget=payload.budget,
        message=payload.message,
        source=payload.source,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(lead)
    await db.flush()

    # Background: notify admins via WhatsApp + ack user via email
    background.add_task(
        whatsapp_service.notify_admins_new_lead,
        payload.full_name, payload.phone, trip_title, payload.message or "",
    )
    if payload.email:
        background.add_task(
            email_service.send_lead_acknowledgement_email,
            payload.email, payload.full_name, trip_title,
        )

    return lead


@router.post("/newsletter", response_model=MessageOut, status_code=201)
async def newsletter_signup(email: str, db: AsyncSession = Depends(get_db)):
    from app.models import NewsletterSubscriber
    existing = (
        await db.execute(select(NewsletterSubscriber).where(NewsletterSubscriber.email == email))
    ).scalar_one_or_none()
    if existing:
        return MessageOut(message="Already subscribed")
    db.add(NewsletterSubscriber(email=email, source="website"))
    return MessageOut(message="Subscribed")
