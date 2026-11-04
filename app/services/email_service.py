"""Transactional email via Gmail SMTP. Free tier: 500 mails/day."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> dict:
    user = getattr(settings, "GMAIL_USER", None) or settings.EMAIL_FROM
    password = getattr(settings, "GMAIL_APP_PASSWORD", None)
    if not password or password == "placeholder":
        logger.warning("GMAIL_APP_PASSWORD not set — email skipped")
        return {"skipped": True}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{user}>"
    msg["To"] = f"{to_name} <{to_email}>"
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(user, password)
            server.send_message(msg)
        logger.info("Email sent to %s", to_email)
        return {"ok": True}
    except Exception as e:
        logger.error("Gmail SMTP failed: %s", e)
        raise


async def send_booking_confirmation_email(to_email, to_name, booking_code, trip_title, start_date, total):
    html = f"""
    <h2>Namaste {to_name},</h2>
    <p>Your Symphony of Summits booking is confirmed. See you on the trail.</p>
    <ul>
      <li><b>Booking Code:</b> {booking_code}</li>
      <li><b>Trip:</b> {trip_title}</li>
      <li><b>Start Date:</b> {start_date}</li>
      <li><b>Amount Paid:</b> ₹{total}</li>
    </ul>
    <p>We'll contact you with joining instructions a week before departure.</p>
    <p>— Team Symphony of Summits</p>
    """
    return await send_email(to_email, to_name, f"Booking Confirmed — {trip_title}", html)


async def send_lead_acknowledgement_email(to_email, to_name, trip_title):
    html = f"""
    <h2>Hi {to_name},</h2>
    <p>Thanks for your interest in <b>{trip_title}</b>. Our team will reach out within a few hours.</p>
    <p>— Team Symphony of Summits</p>
    """
    return await send_email(to_email, to_name, "We've received your enquiry", html)