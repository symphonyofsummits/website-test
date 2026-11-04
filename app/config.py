"""Centralized settings loaded from .env via pydantic-settings."""
from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Symphony of Summits API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_STORAGE_BUCKET: str = "symphony-media"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # PayU
    PAYU_MERCHANT_KEY: str = ""
    PAYU_MERCHANT_SALT: str = ""
    PAYU_MODE: str = "test"
    PAYU_BASE_URL: str = "https://test.payu.in"
    PAYU_WEBHOOK_SECRET: str = ""

    # UPI direct
    UPI_VPA: str = "yourname@okaxis"
    UPI_PAYEE_NAME: str = "Symphony of Summits"
    UPI_MERCHANT_CODE: str = "5411"

    # WhatsApp
    WA_PHONE_NUMBER_ID: str = ""
    WA_ACCESS_TOKEN: str = ""
    WA_VERIFY_TOKEN: str = ""
    WA_BUSINESS_ACCOUNT_ID: str = ""
    WA_ADMIN_NUMBERS: str = ""
    WA_TEMPLATE_BOOKING_CONFIRMED: str = "booking_confirmed"
    WA_TEMPLATE_LEAD_RECEIVED: str = "lead_received"
    WA_TEMPLATE_PAYMENT_RECEIVED: str = "payment_received"

    # Email
        # Email
    EMAIL_PROVIDER: str = "gmail"
    BREVO_API_KEY: str = ""
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    EMAIL_FROM: str = "hello@symphonyofsummits.com"
    EMAIL_FROM_NAME: str = "Symphony of Summits"

    # R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_PUBLIC_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Instagram
    IG_ACCESS_TOKEN: str = ""
    IG_USER_ID: str = ""

    # Admin
    ADMIN_EMAIL: str = "admin@symphonyofsummits.com"
    ADMIN_WHATSAPP: str = ""

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def admin_wa_numbers(self) -> List[str]:
        return [n.strip() for n in self.WA_ADMIN_NUMBERS.split(",") if n.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
