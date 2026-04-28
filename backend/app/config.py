from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    secret_key: str = "change-me-to-a-long-random-string-min-32-chars"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/adops.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Google Ads
    google_ads_developer_token: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_refresh_token: str = ""
    google_ads_login_customer_id: str = ""

    # Demo mode (Google Ads API olmadan mock veriyle çalış)
    demo_mode: bool = True

    # Email
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "adops@example.com"

    # Sentry
    sentry_dsn: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # First admin
    first_admin_email: str = "admin@adops.local"
    first_admin_password: str = "Admin1234!"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
