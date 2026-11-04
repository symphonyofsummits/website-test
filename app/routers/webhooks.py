"""Public webhook endpoints — WhatsApp inbound."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Notification
from app.models.enums import NotificationStatus
from app.services import whatsapp_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    """Meta calls this once to verify webhook ownership."""
    result = whatsapp_service.verify_webhook_challenge(hub_mode, hub_token, hub_challenge)
    if result is None:
        raise HTTPException(403, "Verification failed")
    return int(result)


@router.post("/whatsapp")
async def whatsapp_receive(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Inbound WhatsApp events — delivery status updates and user replies.
    Updates notification rows (status/delivered/read) accordingly.
    """
    payload = await request.json()
    events = whatsapp_service.parse_webhook_event(payload)

    for ev in events:
        if ev["type"] == "status" and ev.get("message_id"):
            notif = (
                await db.execute(select(Notification).where(
                    Notification.provider_message_id == ev["message_id"]
                ))
            ).scalar_one_or_none()
            if notif:
                mapping = {
                    "sent": NotificationStatus.SENT,
                    "delivered": NotificationStatus.DELIVERED,
                    "read": NotificationStatus.READ,
                    "failed": NotificationStatus.FAILED,
                }
                new_status = mapping.get(ev["status"])
                if new_status:
                    notif.status = new_status
                    if ev["status"] == "delivered":
                        notif.delivered_at = datetime.now(timezone.utc)
                    elif ev["status"] == "read":
                        notif.read_at = datetime.now(timezone.utc)
        elif ev["type"] == "message":
            # Log the inbound message — a human will reply from the dashboard
            logger.info("Inbound WA from %s: %s", ev["from"], ev["text"])

    return {"ok": True}
