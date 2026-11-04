"""
PayU UPI QR integration — generates a dynamic UPI payment QR.

Strategy:
- Generate a UPI deep-link URI ourselves (upi://pay?...)
- Render it as a PNG QR code, return base64 to frontend
- On the booking, store the txn ref in the Payment row
- Verification happens via:
    (a) user enters UTR after paying → manual verify endpoint
    (b) PayU webhook POSTs here when they settle → auto verify
"""
import base64
import hashlib
import hmac
import io
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from urllib.parse import quote

import qrcode

from app.config import settings


def generate_txn_ref(prefix: str = "SOS") -> str:
    """Short unique txn reference, e.g. SOS20261103ABCD1234."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand = secrets.token_hex(4).upper()
    return f"{prefix}{stamp}{rand}"


def build_upi_uri(
    amount: Decimal,
    txn_ref: str,
    note: str = "Symphony of Summits Booking",
    vpa: Optional[str] = None,
    payee_name: Optional[str] = None,
) -> str:
    """
    Build a standards-compliant UPI deep link.
    Spec: pa (payee VPA), pn (payee name), am (amount), tn (txn note), tr (txn ref), cu (currency), mc (MCC)
    """
    vpa = vpa or settings.UPI_VPA
    payee_name = payee_name or settings.UPI_PAYEE_NAME
    params = {
        "pa": vpa,
        "pn": payee_name,
        "am": f"{amount:.2f}",
        "cu": "INR",
        "tn": note,
        "tr": txn_ref,
        "mc": settings.UPI_MERCHANT_CODE,
    }
    qs = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
    return f"upi://pay?{qs}"


def generate_qr_png_base64(upi_uri: str, size: int = 10, border: int = 2) -> str:
    """Render UPI URI as a QR PNG and return base64 (data URI friendly)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size,
        border=border,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def generate_payment_qr(amount: Decimal, booking_code: str) -> dict:
    """
    Create a complete QR payment payload for a booking.
    Returns a dict ready to drop into PaymentQRResponse.
    """
    txn_ref = generate_txn_ref()
    note = f"SOS {booking_code}"
    upi_uri = build_upi_uri(amount=amount, txn_ref=txn_ref, note=note)
    qr_b64 = generate_qr_png_base64(upi_uri)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    return {
        "amount": amount,
        "currency": "INR",
        "upi_vpa": settings.UPI_VPA,
        "upi_payee_name": settings.UPI_PAYEE_NAME,
        "upi_uri": upi_uri,
        "qr_png_base64": qr_b64,
        "txn_ref": txn_ref,
        "expires_at": expires_at,
    }


# ---------------- PAYU WEBHOOK VERIFICATION ----------------
def verify_payu_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    PayU sends an HMAC-SHA256 signature in the X-PayU-Signature header.
    We verify with our shared webhook secret.
    """
    if not settings.PAYU_WEBHOOK_SECRET:
        return False
    expected = hmac.new(
        settings.PAYU_WEBHOOK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def payu_hash(data: dict) -> str:
    """
    PayU standard hash for form posts:
    sha512(key|txnid|amount|productinfo|firstname|email|||||||||||salt)
    """
    key = settings.PAYU_MERCHANT_KEY
    salt = settings.PAYU_MERCHANT_SALT
    raw = (
        f"{key}|{data.get('txnid', '')}|{data.get('amount', '')}|"
        f"{data.get('productinfo', '')}|{data.get('firstname', '')}|"
        f"{data.get('email', '')}|||||||||||{salt}"
    )
    return hashlib.sha512(raw.encode("utf-8")).hexdigest()
