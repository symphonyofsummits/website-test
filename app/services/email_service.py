"""Transactional email via Brevo (ex-Sendinblue). Free tier: 300 mails/day."""
import logging
from typing import Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

BREVO_API = "https://api.brevo.com/v3/smtp/email"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    cc: Optional[List[Dict[str, str]]] = None,
) -> Dict:
    if not settings.BREVO_API_KEY:
        logger.warning("BREVO_API_KEY not set — email skipped")
        return {"skipped": True}

    payload = {
        "sender": {"name": settings.EMAIL_FROM_NAME, "email": settings.EMAIL_FROM},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_body,
    }
    if text_body:
        payload["textContent"] = text_body
    if cc:
        payload["cc"] = cc

    headers = {
        "api-key": settings.BREVO_API_KEY,
        "accept": "application/json",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(BREVO_API, headers=headers, json=payload)
        if r.status_code >= 400:
            logger.error("Brevo email failed %s: %s", r.status_code, r.text)
            r.raise_for_status()
        return r.json()


# ---------------- CANNED EMAILS ----------------
async def send_booking_confirmation_email(
    to_email: str, to_name: str, booking_code: str, trip_title: str, start_date: str, total: str,
):
    html = f"""
    <h2>Namaste {to_name},</h2>
    <p>Your Symphony of Summits booking is confirmed. See you on the trail.</p>
    <ul>
      <li><b>Booking Code:</b> {booking_code}</li>
      <li><b>Trip:</b> {trip_title}</li>
      <li><b>Start Date:</b> {start_date}</li>
      <li><b>Amount Paid:</b> ₹{total}</li>
    </ul>
    <p>We'll WhatsApp you joining instructions a week before departure.</p>
    <p>— Team Symphony of Summits</p>
    """
    return await send_email(to_email, to_name, f"Booking Confirmed — {trip_title}", html)


async def send_lead_acknowledgement_email(to_email: str, to_name: str, trip_title: str):
    html = f"""
    <h2>Hi {to_name},</h2>
    <p>Thanks for your interest in <b>{trip_title}</b>. Our team will reach out within a few hours.</p>
    <p>— Team Symphony of Summits</p>
    """
    return await send_email(to_email, to_name, "We've received your enquiry", html)
