"""Payment endpoints — UPI QR generation and manual verification."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Booking, Payment, Trip, User
from app.models.enums import BookingStatus, PaymentMethod, PaymentStatus
from app.schemas.schemas import (
    PaymentInitiateIn, PaymentOut, PaymentQRResponse, PaymentVerifyIn,
)
from app.security import get_current_user, require_admin
from app.services import booking_service, payu_service, whatsapp_service, email_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/initiate", response_model=PaymentQRResponse)
async def initiate_payment(
    payload: PaymentInitiateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Payment row (status=pending) and return a UPI QR for the user to scan.
    The frontend shows the QR; after paying, user enters the UTR in /verify.
    """
    booking = (
        await db.execute(select(Booking).where(Booking.id == payload.booking_id, Booking.user_id == user.id))
    ).scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise HTTPException(400, f"Cannot pay for a {booking.status} booking")

    trip = (await db.execute(select(Trip).where(Trip.id == booking.trip_id))).scalar_one()

    # If advance only, cap the amount at the trip's advance_amount
    amount = payload.amount
    if payload.is_advance and amount > trip.advance_amount:
        amount = Decimal(trip.advance_amount)

    qr_data = payu_service.generate_payment_qr(amount, booking.booking_code)

    payment = Payment(
        booking_id=booking.id,
        user_id=user.id,
        amount=amount,
        currency="INR",
        method=PaymentMethod.UPI_QR,
        status=PaymentStatus.PENDING,
        is_advance=payload.is_advance,
        gateway="upi_direct",
        upi_vpa=qr_data["upi_vpa"],
        gateway_order_id=qr_data["txn_ref"],
    )
    db.add(payment)
    await db.flush()

    return PaymentQRResponse(
        payment_id=payment.id,
        amount=amount,
        currency="INR",
        upi_vpa=qr_data["upi_vpa"],
        upi_payee_name=qr_data["upi_payee_name"],
        upi_uri=qr_data["upi_uri"],
        qr_png_base64=qr_data["qr_png_base64"],
        txn_ref=qr_data["txn_ref"],
        expires_at=qr_data["expires_at"],
        status=PaymentStatus.PENDING,
    )


@router.post("/verify", response_model=PaymentOut)
async def verify_payment(
    payload: PaymentVerifyIn,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    User-submitted UTR after they paid. We mark the payment as 'processing'
    (not success yet — admin verifies). This still returns the record so the
    frontend can show 'payment under review' state.
    """
    payment = (
        await db.execute(select(Payment).where(Payment.id == payload.payment_id, Payment.user_id == user.id))
    ).scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(400, f"Payment is already {payment.status}")

    payment.upi_txn_ref = payload.upi_txn_ref
    payment.upi_screenshot_url = payload.upi_screenshot_url
    payment.status = PaymentStatus.PROCESSING

    # Fire-and-forget admin alert
    booking = (await db.execute(select(Booking).where(Booking.id == payment.booking_id))).scalar_one()
    background.add_task(_notify_admin_payment_pending, booking.booking_code, user.full_name, payment.amount, payload.upi_txn_ref)

    return payment


@router.post("/admin/{payment_id}/approve", response_model=PaymentOut)
async def admin_approve_payment(
    payment_id: UUID,
    background: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin confirms the UPI payment landed. This triggers booking confirmation + user notifications."""
    payment = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status == PaymentStatus.SUCCESS:
        raise HTTPException(400, "Already approved")

    payment.status = PaymentStatus.SUCCESS
    payment.manually_verified_by = admin.id
    payment.manually_verified_at = datetime.now(timezone.utc)
    payment.completed_at = datetime.now(timezone.utc)

    booking = (await db.execute(select(Booking).where(Booking.id == payment.booking_id))).scalar_one()
    await booking_service.confirm_booking(db, booking, payment.amount)

    customer = (await db.execute(select(User).where(User.id == booking.user_id))).scalar_one()
    trip = (await db.execute(select(Trip).where(Trip.id == booking.trip_id))).scalar_one()

    background.add_task(
        _notify_user_booking_confirmed_bg,
        customer.phone, customer.email, customer.full_name,
        booking.booking_code, trip.title, str(booking.total_amount),
    )
    return payment


@router.post("/admin/{payment_id}/reject", response_model=PaymentOut)
async def admin_reject_payment(
    payment_id: UUID,
    reason: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    payment = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")
    payment.status = PaymentStatus.FAILED
    payment.failure_reason = reason
    return payment


# ---------------- WEBHOOK (optional, for when PayU plugged in) ----------------
@router.post("/webhook/payu", include_in_schema=False)
async def payu_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-PayU-Signature", "")
    if not payu_service.verify_payu_webhook_signature(body, signature):
        raise HTTPException(401, "Invalid signature")

    data = await request.json()
    txn_ref = data.get("txnid")
    status_str = data.get("status")

    payment = (
        await db.execute(select(Payment).where(Payment.gateway_order_id == txn_ref))
    ).scalar_one_or_none()
    if not payment:
        return {"ok": True}

    payment.gateway_response = data
    if status_str == "success":
        payment.status = PaymentStatus.SUCCESS
        payment.completed_at = datetime.now(timezone.utc)
        booking = (await db.execute(select(Booking).where(Booking.id == payment.booking_id))).scalar_one()
        await booking_service.confirm_booking(db, booking, payment.amount)
    else:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = status_str
    return {"ok": True}


# ---------------- BACKGROUND HELPERS ----------------
async def _notify_admin_payment_pending(booking_code, name, amount, txn_ref):
    from app.config import settings
    for admin in settings.admin_wa_numbers:
        try:
            await whatsapp_service.send_text(
                admin,
                f"New UPI payment pending verification\n"
                f"Booking: {booking_code}\nCustomer: {name}\n"
                f"Amount: ₹{amount}\nUTR: {txn_ref}",
            )
        except Exception:
            pass


async def _notify_user_booking_confirmed_bg(phone, email, name, booking_code, trip_title, total):
    try:
        if phone:
            await whatsapp_service.notify_user_booking_confirmed(
                phone, name, booking_code, trip_title, str(datetime.now().date()), total,
            )
    except Exception:
        pass
    try:
        if email:
            await email_service.send_booking_confirmation_email(
                email, name, booking_code, trip_title, str(datetime.now().date()), total,
            )
    except Exception:
        pass
