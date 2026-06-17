import secrets
from functools import lru_cache
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    DATABASE_URL: str = "postgresql+asyncpg://procure:procure@localhost:5432/procurewatch"
    REDIS_URL: str = "redis://localhost:6379"
    ANTHROPIC_API_KEY: str = ""
    SCRAPE_PROXY_URL: str = ""
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://frontend:3000"]
    API_KEY_HEADER: str = "X-API-Key"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_REPORTS_PER_DAY: int = 10

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = "price_pro_monthly"
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: str = ""

    # Resend
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "alerts@procurewatch.in"

    # Auth
    ADMIN_API_KEY: str = "procurewatch-admin-secret"

    # Monitoring
    SENTRY_DSN: str = ""

    # Storage (Cloudflare R2 for PDF/backup exports)
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY: str = ""
    R2_SECRET_KEY: str = ""
    R2_BUCKET: str = "procurewatch-exports"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
