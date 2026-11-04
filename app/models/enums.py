"""Python mirrors of Postgres enums. Keep in sync with schema.sql."""
from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "customer"
    GUIDE = "guide"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class IdProofType(str, Enum):
    AADHAAR = "aadhaar"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    VOTER_ID = "voter_id"
    PAN = "pan"


class TripCategory(str, Enum):
    TREK = "trek"
    EXPEDITION = "expedition"
    PILGRIMAGE = "pilgrimage"
    PACKAGE = "package"
    ADVENTURE = "adventure"
    HILLSTATION = "hillstation"


class TripScope(str, Enum):
    INDIAN = "indian"
    INTERNATIONAL = "international"


class Difficulty(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    EXTREME = "extreme"


class BatchStatus(str, Enum):
    OPEN = "open"
    FILLING_FAST = "filling_fast"
    FEW_SEATS_LEFT = "few_seats_left"
    SOLD_OUT = "sold_out"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    UPI_QR = "upi_qr"
    PAYU = "payu"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"


class LeadSource(str, Enum):
    WEBSITE_FORM = "website_form"
    QUOTE_MODAL = "quote_modal"
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE_ADS = "google_ads"
    REFERRAL = "referral"
    WALK_IN = "walk_in"
    OTHER = "other"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    QUOTED = "quoted"
    CONVERTED = "converted"
    LOST = "lost"
    SPAM = "spam"


class NotificationChannel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class StoryStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class GearCategory(str, Enum):
    BACKPACK = "backpack"
    FOOTWEAR = "footwear"
    CLOTHING = "clothing"
    SLEEPING = "sleeping"
    NAVIGATION = "navigation"
    SAFETY = "safety"
    COOKING = "cooking"
    CLIMBING = "climbing"
    ACCESSORIES = "accessories"
