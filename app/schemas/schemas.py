"""Pydantic v2 request/response schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import (
    BatchStatus, BookingStatus, Difficulty, Gender, IdProofType, LeadSource,
    LeadStatus, PaymentMethod, PaymentStatus, TripCategory, TripScope, UserRole,
)


# ---------------- COMMON ----------------
class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


# ---------------- AUTH ----------------
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=10, max_length=20)

    @field_validator("phone")
    @classmethod
    def _norm_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.startswith("+") and len(v) == 10:
            v = "+91" + v
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshIn(BaseModel):
    refresh_token: str


class OTPRequestIn(BaseModel):
    phone: str


class OTPVerifyIn(BaseModel):
    phone: str
    otp: str = Field(..., min_length=4, max_length=8)


# ---------------- USER ----------------
class UserOut(ORMBase):
    id: UUID
    email: EmailStr
    phone: Optional[str] = None
    full_name: str
    role: UserRole
    avatar_url: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    phone_verified_at: Optional[datetime] = None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    nationality: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_rel: Optional[str] = None


# ---------------- TRIP ----------------
class TripListOut(ORMBase):
    id: UUID
    slug: str
    title: str
    subtitle: Optional[str] = None
    category: TripCategory
    scope: TripScope
    difficulty: Optional[Difficulty] = None
    region: Optional[str] = None
    country: str
    duration_days: int
    max_altitude_m: Optional[int] = None
    base_price: Decimal
    discount_pct: Decimal
    cover_image: Optional[str] = None
    is_featured: bool
    highlights: Optional[List[str]] = None


class TripDetailOut(TripListOut):
    overview_md: Optional[str] = None
    itinerary: Optional[Any] = None
    inclusions: Optional[List[str]] = None
    exclusions: Optional[List[str]] = None
    things_to_carry: Optional[List[str]] = None
    faqs: Optional[Any] = None
    gallery: Optional[List[str]] = None
    trailer_video_url: Optional[str] = None
    advance_amount: Decimal
    gst_pct: Decimal
    min_age: int
    max_age: int
    fitness_level: Optional[str] = None
    technical_grade: Optional[str] = None
    base_camp: Optional[str] = None
    trek_distance_km: Optional[Decimal] = None


class TripCreate(BaseModel):
    slug: str
    title: str
    subtitle: Optional[str] = None
    category: TripCategory
    scope: TripScope = TripScope.INDIAN
    difficulty: Optional[Difficulty] = None
    region: Optional[str] = None
    country: str = "India"
    duration_days: int = Field(..., gt=0, le=60)
    max_altitude_m: Optional[int] = None
    base_price: Decimal
    advance_amount: Decimal = Decimal("2000")
    short_description: Optional[str] = None
    cover_image: Optional[str] = None
    gallery: Optional[List[str]] = None
    itinerary: Optional[Any] = None
    inclusions: Optional[List[str]] = None
    exclusions: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    is_published: bool = False
    is_featured: bool = False


class TripFilter(BaseModel):
    category: Optional[TripCategory] = None
    scope: Optional[TripScope] = None
    difficulty: Optional[Difficulty] = None
    region: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    duration_min: Optional[int] = None
    duration_max: Optional[int] = None
    search: Optional[str] = None
    featured_only: bool = False


# ---------------- BATCH ----------------
class BatchOut(ORMBase):
    id: UUID
    trip_id: UUID
    batch_code: Optional[str] = None
    start_date: date
    end_date: date
    total_seats: int
    booked_seats: int
    reserved_seats: int
    price_override: Optional[Decimal] = None
    status: BatchStatus
    seats_available: int

    @field_validator("seats_available", mode="before")
    @classmethod
    def _calc_available(cls, v, info):
        if v is not None:
            return v
        d = info.data
        return d.get("total_seats", 0) - d.get("booked_seats", 0) - d.get("reserved_seats", 0)


class BatchCreate(BaseModel):
    trip_id: UUID
    start_date: date
    end_date: date
    total_seats: int = Field(..., gt=0, le=200)
    price_override: Optional[Decimal] = None
    pickup_point: Optional[str] = None
    dropoff_point: Optional[str] = None


# ---------------- BOOKING ----------------
class TravellerIn(BaseModel):
    is_lead: bool = False
    full_name: str
    age: int = Field(..., gt=0, lt=120)
    gender: Optional[Gender] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    id_proof_type: Optional[IdProofType] = None
    id_proof_number: Optional[str] = None
    medical_conditions: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class TravellerOut(ORMBase):
    id: UUID
    full_name: str
    age: Optional[int] = None
    gender: Optional[Gender] = None
    is_lead: bool


class BookingCreate(BaseModel):
    batch_id: UUID
    travellers: List[TravellerIn] = Field(..., min_length=1, max_length=20)
    coupon_code: Optional[str] = None
    special_requests: Optional[str] = None
    pickup_point: Optional[str] = None


class BookingOut(ORMBase):
    id: UUID
    booking_code: str
    user_id: UUID
    trip_id: UUID
    batch_id: UUID
    travellers_count: int
    base_amount: Decimal
    discount_amount: Decimal
    gst_amount: Decimal
    total_amount: Decimal
    advance_paid: Decimal
    balance_due: Decimal
    status: BookingStatus
    created_at: datetime
    travellers: List[TravellerOut] = []


# ---------------- PAYMENT ----------------
class PaymentInitiateIn(BaseModel):
    booking_id: UUID
    amount: Decimal
    is_advance: bool = True
    method: PaymentMethod = PaymentMethod.UPI_QR


class PaymentQRResponse(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: str = "INR"
    upi_vpa: str
    upi_payee_name: str
    upi_uri: str
    qr_png_base64: str
    txn_ref: str
    expires_at: datetime
    status: PaymentStatus


class PaymentVerifyIn(BaseModel):
    payment_id: UUID
    upi_txn_ref: str = Field(..., min_length=4)
    upi_screenshot_url: Optional[str] = None


class PaymentOut(ORMBase):
    id: UUID
    booking_id: UUID
    amount: Decimal
    method: PaymentMethod
    status: PaymentStatus
    invoice_number: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ---------------- LEAD ----------------
class LeadCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=10)
    city: Optional[str] = None
    interested_trip_id: Optional[UUID] = None
    travellers_count: Optional[int] = None
    preferred_date: Optional[date] = None
    budget: Optional[Decimal] = None
    message: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE_FORM
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class LeadOut(ORMBase):
    id: UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: LeadStatus
    source: LeadSource
    created_at: datetime


# ---------------- STORY ----------------
class StoryListOut(ORMBase):
    id: UUID
    slug: str
    title: str
    subtitle: Optional[str] = None
    cover_image: Optional[str] = None
    excerpt: Optional[str] = None
    category: Optional[str] = None
    reading_minutes: Optional[int] = None
    published_at: Optional[datetime] = None


class StoryDetailOut(StoryListOut):
    body_md: str
    tags: Optional[List[str]] = None
    view_count: int


# ---------------- INSTAGRAM ----------------
class InstagramPostOut(ORMBase):
    id: UUID
    ig_media_id: str
    media_type: Optional[str] = None
    media_url: str
    thumbnail_url: Optional[str] = None
    permalink: Optional[str] = None
    caption: Optional[str] = None
    posted_at: Optional[datetime] = None


# ---------------- WEBHOOK ----------------
class WhatsAppWebhookIn(BaseModel):
    object: str
    entry: List[Any]


# ---------------- GENERIC RESPONSE ----------------
class MessageOut(BaseModel):
    message: str
    detail: Optional[str] = None
