from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://procure:procure@localhost:5432/procurewatch"
    REDIS_URL: str = "redis://localhost:6379"
    ANTHROPIC_API_KEY: str = ""
    SCRAPE_PROXY_URL: str = ""
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
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

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
