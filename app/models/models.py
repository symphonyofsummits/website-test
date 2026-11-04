"""SQLAlchemy ORM models mapped 1:1 to schema.sql."""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY, BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey,
    Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import CITEXT, ENUM as PgEnum, INET, JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import (
    BatchStatus, BookingStatus, Difficulty, GearCategory, Gender, IdProofType, LeadSource,
    LeadStatus, NotificationChannel, NotificationStatus, PaymentMethod,
    PaymentStatus, StoryStatus, TripCategory, TripScope, UserRole,
)


def _pg_enum(enum_cls, name):
    return PgEnum(enum_cls, name=name, create_type=False, values_callable=lambda e: [m.value for m in e])


# =========================================================================
# 1. USERS
# =========================================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    auth_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), unique=True)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    dob: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[Gender]] = mapped_column(_pg_enum(Gender, "gender_type"))
    nationality: Mapped[str] = mapped_column(String(60), default="Indian")
    role: Mapped[UserRole] = mapped_column(_pg_enum(UserRole, "user_role"), default=UserRole.CUSTOMER)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    address_line1: Mapped[Optional[str]] = mapped_column(String(200))
    address_line2: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]] = mapped_column(String(80))
    state: Mapped[Optional[str]] = mapped_column(String(80))
    country: Mapped[str] = mapped_column(String(80), default="India")
    pincode: Mapped[Optional[str]] = mapped_column(String(12))
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(120))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    emergency_contact_rel: Mapped[Optional[str]] = mapped_column(String(40))
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    whatsapp_opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    bookings: Mapped[List["Booking"]] = relationship(back_populates="user", foreign_keys="Booking.user_id")
    documents: Mapped[List["UserDocument"]] = relationship(
        back_populates="user", foreign_keys="UserDocument.user_id", cascade="all, delete-orphan"
    )


class UserDocument(Base):
    __tablename__ = "user_documents"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    doc_type: Mapped[IdProofType] = mapped_column(_pg_enum(IdProofType, "id_proof_type"))
    doc_number: Mapped[Optional[str]] = mapped_column(String(50))
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_on: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="documents", foreign_keys=[user_id])


# =========================================================================
# 2. CATALOG
# =========================================================================
class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(300))
    category: Mapped[TripCategory] = mapped_column(_pg_enum(TripCategory, "trek_category"), nullable=False)
    scope: Mapped[TripScope] = mapped_column(_pg_enum(TripScope, "trek_scope"), default=TripScope.INDIAN)
    difficulty: Mapped[Optional[Difficulty]] = mapped_column(_pg_enum(Difficulty, "difficulty_level"))
    region: Mapped[Optional[str]] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(80), default="India")
    state: Mapped[Optional[str]] = mapped_column(String(80))
    base_camp: Mapped[Optional[str]] = mapped_column(String(120))
    duration_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    duration_nights: Mapped[Optional[int]] = mapped_column(SmallInteger)
    max_altitude_m: Mapped[Optional[int]] = mapped_column(Integer)
    trek_distance_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    best_season: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    advance_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=2000)
    gst_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=5.00)
    currency: Mapped[str] = mapped_column(String(3), default="INR")

    short_description: Mapped[Optional[str]] = mapped_column(Text)
    overview_md: Mapped[Optional[str]] = mapped_column(Text)
    itinerary: Mapped[Optional[dict]] = mapped_column(JSONB)
    inclusions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    exclusions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    things_to_carry: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    highlights: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    faqs: Mapped[Optional[dict]] = mapped_column(JSONB)

    cover_image: Mapped[Optional[str]] = mapped_column(Text)
    gallery: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    trailer_video_url: Mapped[Optional[str]] = mapped_column(Text)
    gpx_file_url: Mapped[Optional[str]] = mapped_column(Text)
    brochure_pdf_url: Mapped[Optional[str]] = mapped_column(Text)

    min_age: Mapped[int] = mapped_column(SmallInteger, default=10)
    max_age: Mapped[int] = mapped_column(SmallInteger, default=65)
    fitness_level: Mapped[Optional[str]] = mapped_column(Text)
    medical_requirements: Mapped[Optional[str]] = mapped_column(Text)
    technical_grade: Mapped[Optional[str]] = mapped_column(String(20))

    seo_title: Mapped[Optional[str]] = mapped_column(String(200))
    seo_description: Mapped[Optional[str]] = mapped_column(String(300))
    seo_keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    batches: Mapped[List["Batch"]] = relationship(back_populates="trip", cascade="all, delete-orphan")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    trip_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"))
    batch_code: Mapped[Optional[str]] = mapped_column(String(40), unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_seats: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    booked_seats: Mapped[int] = mapped_column(SmallInteger, default=0)
    reserved_seats: Mapped[int] = mapped_column(SmallInteger, default=0)
    price_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    status: Mapped[BatchStatus] = mapped_column(_pg_enum(BatchStatus, "batch_status"), default=BatchStatus.OPEN)
    lead_guide_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    pickup_point: Mapped[Optional[str]] = mapped_column(String(200))
    dropoff_point: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trip: Mapped["Trip"] = relationship(back_populates="batches")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="batch")

    @property
    def seats_available(self) -> int:
        return self.total_seats - self.booked_seats - self.reserved_seats


# =========================================================================
# 3. BOOKINGS
# =========================================================================
class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    booking_code: Mapped[str] = mapped_column(String(20), unique=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    trip_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("trips.id"))
    batch_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("batches.id"))
    travellers_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    advance_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    balance_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[BookingStatus] = mapped_column(_pg_enum(BookingStatus, "booking_status"), default=BookingStatus.PENDING)
    coupon_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("coupons.id"))
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    pickup_point: Mapped[Optional[str]] = mapped_column(String(200))
    booked_from_ip: Mapped[Optional[str]] = mapped_column(INET)
    booked_from_source: Mapped[Optional[LeadSource]] = mapped_column(_pg_enum(LeadSource, "lead_source"))
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="bookings", foreign_keys=[user_id])
    trip: Mapped["Trip"] = relationship()
    batch: Mapped["Batch"] = relationship(back_populates="bookings")
    travellers: Mapped[List["Traveller"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="booking")


class Traveller(Base):
    __tablename__ = "travellers"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    booking_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"))
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[Optional[int]] = mapped_column(SmallInteger)
    gender: Mapped[Optional[Gender]] = mapped_column(_pg_enum(Gender, "gender_type"))
    nationality: Mapped[Optional[str]] = mapped_column(String(60))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(CITEXT)
    id_proof_type: Mapped[Optional[IdProofType]] = mapped_column(_pg_enum(IdProofType, "id_proof_type"))
    id_proof_number: Mapped[Optional[str]] = mapped_column(String(50))
    id_proof_url: Mapped[Optional[str]] = mapped_column(Text)
    medical_conditions: Mapped[Optional[str]] = mapped_column(Text)
    blood_group: Mapped[Optional[str]] = mapped_column(String(5))
    dietary_needs: Mapped[Optional[str]] = mapped_column(String(100))
    tshirt_size: Mapped[Optional[str]] = mapped_column(String(10))
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(120))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    insurance_policy_no: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped["Booking"] = relationship(back_populates="travellers")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    booking_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("bookings.id", ondelete="RESTRICT"))
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    method: Mapped[PaymentMethod] = mapped_column(_pg_enum(PaymentMethod, "payment_method"))
    status: Mapped[PaymentStatus] = mapped_column(_pg_enum(PaymentStatus, "payment_status"), default=PaymentStatus.PENDING)
    is_advance: Mapped[bool] = mapped_column(Boolean, default=False)

    gateway: Mapped[Optional[str]] = mapped_column(String(30))
    gateway_order_id: Mapped[Optional[str]] = mapped_column(String(80))
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(String(80))
    gateway_signature: Mapped[Optional[str]] = mapped_column(Text)
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSONB)

    upi_vpa: Mapped[Optional[str]] = mapped_column(String(80))
    upi_txn_ref: Mapped[Optional[str]] = mapped_column(String(60))
    upi_screenshot_url: Mapped[Optional[str]] = mapped_column(Text)
    manually_verified_by: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    manually_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    invoice_number: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    invoice_url: Mapped[Optional[str]] = mapped_column(Text)
    receipt_url: Mapped[Optional[str]] = mapped_column(Text)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped["Booking"] = relationship(back_populates="payments")


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(String(10))
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    min_order_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# =========================================================================
# 4. LEADS, NOTIFICATIONS, STORIES
# =========================================================================
class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(CITEXT)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    city: Mapped[Optional[str]] = mapped_column(String(80))
    interested_trip_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("trips.id"))
    travellers_count: Mapped[Optional[int]] = mapped_column(SmallInteger)
    preferred_date: Mapped[Optional[date]] = mapped_column(Date)
    budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    message: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[LeadSource] = mapped_column(_pg_enum(LeadSource, "lead_source"), default=LeadSource.WEBSITE_FORM)
    status: Mapped[LeadStatus] = mapped_column(_pg_enum(LeadStatus, "lead_status"), default=LeadStatus.NEW)
    assigned_to: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    utm_source: Mapped[Optional[str]] = mapped_column(String(80))
    utm_medium: Mapped[Optional[str]] = mapped_column(String(80))
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(80))
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    whatsapp_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    first_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    converted_booking_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("bookings.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    lead_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("leads.id"))
    booking_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("bookings.id"))
    channel: Mapped[NotificationChannel] = mapped_column(_pg_enum(NotificationChannel, "notification_channel"))
    template_name: Mapped[Optional[str]] = mapped_column(String(80))
    recipient: Mapped[str] = mapped_column(String(120), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(200))
    body: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    provider: Mapped[Optional[str]] = mapped_column(String(40))
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(120))
    status: Mapped[NotificationStatus] = mapped_column(_pg_enum(NotificationStatus, "notification_status"), default=NotificationStatus.QUEUED)
    error: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(300))
    cover_image: Mapped[Optional[str]] = mapped_column(Text)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(String(400))
    author_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    trip_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("trips.id"))
    category: Mapped[Optional[str]] = mapped_column(String(60))
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    reading_minutes: Mapped[Optional[int]] = mapped_column(SmallInteger)
    status: Mapped[StoryStatus] = mapped_column(_pg_enum(StoryStatus, "story_status"), default=StoryStatus.DRAFT)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    seo_title: Mapped[Optional[str]] = mapped_column(String(200))
    seo_description: Mapped[Optional[str]] = mapped_column(String(300))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# =========================================================================
# 5. GEAR
# =========================================================================
class GearItem(Base):
    __tablename__ = "gear_items"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    sku: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[GearCategory] = mapped_column(_pg_enum(GearCategory, "gear_category"))
    brand: Mapped[Optional[str]] = mapped_column(String(80))
    description: Mapped[Optional[str]] = mapped_column(Text)
    size: Mapped[Optional[str]] = mapped_column(String(20))
    color: Mapped[Optional[str]] = mapped_column(String(40))
    daily_rent: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    weekly_rent: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    deposit: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    total_stock: Mapped[int] = mapped_column(SmallInteger, default=0)
    available_stock: Mapped[int] = mapped_column(SmallInteger, default=0)
    image_urls: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# =========================================================================
# 6. INSTAGRAM CACHE
# =========================================================================
class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    ig_media_id: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    media_type: Mapped[Optional[str]] = mapped_column(String(20))
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text)
    permalink: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(60))
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id"))
    trip_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("trips.id"))
    booking_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("bookings.id"))
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    body: Mapped[Optional[str]] = mapped_column(Text)
    images: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_from_admin: Mapped[Optional[str]] = mapped_column(Text)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
