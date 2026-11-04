"""
WhatsApp Cloud API (Meta) — send templates, verify webhooks, dispatch admin alerts.

Setup (one-time):
1. Meta Business → WhatsApp Business → add phone number
2. Create message templates (lead_received, booking_confirmed, payment_received) and get them approved
3. Grab Phone Number ID + Permanent Access Token
4. Set them in .env (WA_PHONE_NUMBER_ID, WA_ACCESS_TOKEN, WA_VERIFY_TOKEN)
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

WA_API = "https://graph.facebook.com/v21.0"


def _normalize_phone(phone: str) -> str:
    """Meta wants numbers like 919999999999 — no +, no spaces."""
    p = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if len(p) == 10 and not p.startswith("91"):
        p = "91" + p
    return p


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _send(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{WA_API}/{settings.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            logger.error("WhatsApp API error %s: %s", r.status_code, r.text)
            r.raise_for_status()
        return r.json()


async def send_text(to: str, body: str) -> Dict[str, Any]:
    """Simple session message (only works within the 24h customer-service window)."""
    return await _send({
        "messaging_product": "whatsapp",
        "to": _normalize_phone(to),
        "type": "text",
        "text": {"body": body},
    })


async def send_template(
    to: str,
    template_name: str,
    language: str = "en",
    variables: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Pre-approved template — works outside the 24h window and is used for proactive messages."""
    components = []
    if variables:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": str(v)} for v in variables],
        })
    payload = {
        "messaging_product": "whatsapp",
        "to": _normalize_phone(to),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": components,
        },
    }
    return await _send(payload)


# ---------------- HIGH-LEVEL BUSINESS CALLS ----------------
async def notify_admins_new_lead(lead_name: str, lead_phone: str, trip: str, message: str) -> None:
    """Fire off a message to every admin number listed in config when a lead comes in."""
    for admin in settings.admin_wa_numbers:
        try:
            await send_template(
                to=admin,
                template_name=settings.WA_TEMPLATE_LEAD_RECEIVED,
                variables=[lead_name, lead_phone, trip, message[:200]],
            )
        except Exception as e:
            logger.error("Admin WA notify failed for %s: %s", admin, e)


async def notify_user_booking_confirmed(
    user_phone: str, user_name: str, booking_code: str, trip_title: str, start_date: str, total: str,
) -> Dict[str, Any]:
    return await send_template(
        to=user_phone,
        template_name=settings.WA_TEMPLATE_BOOKING_CONFIRMED,
        variables=[user_name, booking_code, trip_title, start_date, total],
    )


async def notify_user_payment_received(
    user_phone: str, user_name: str, amount: str, booking_code: str,
) -> Dict[str, Any]:
    return await send_template(
        to=user_phone,
        template_name=settings.WA_TEMPLATE_PAYMENT_RECEIVED,
        variables=[user_name, amount, booking_code],
    )


# ---------------- WEBHOOK VERIFICATION ----------------
def verify_webhook_challenge(mode: str, token: str, challenge: str) -> Optional[str]:
    """GET request Meta sends to verify your webhook URL."""
    if mode == "subscribe" and token == settings.WA_VERIFY_TOKEN:
        return challenge
    return None


def parse_webhook_event(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract flat events from Meta's nested webhook payload.
    Returns [{type: 'status'|'message', from, text, message_id, status, timestamp}, ...]
    """
    events = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []) or []:
                events.append({
                    "type": "message",
                    "from": msg.get("from"),
                    "message_id": msg.get("id"),
                    "text": msg.get("text", {}).get("body"),
                    "timestamp": msg.get("timestamp"),
                })
            for status in value.get("statuses", []) or []:
                events.append({
                    "type": "status",
                    "message_id": status.get("id"),
                    "status": status.get("status"),  # sent | delivered | read | failed
                    "timestamp": status.get("timestamp"),
                })
    return events
