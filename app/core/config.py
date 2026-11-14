# File: app/core/config.py
import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot_kripto.db"
    TELEGRAM_BOT_TOKEN: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-6.1-sol"
    OPENAI_DAILY_TOKEN_LIMIT: int = Field(default=200_000, ge=0, le=200_000)
    OPENAI_MAX_OUTPUT_TOKENS: int = Field(default=2048, ge=256, le=8192)
    OPENAI_BUDGET_DB: str = ".local/openai_budget.sqlite3"
    OPENAI_HTTP_EXPLANATIONS_ENABLED: bool = False
    ETHERSCAN_API_KEY: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    STRIPE_API_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PRICE_IDS: dict[str, str] = Field(default_factory=dict)
    DOMAIN: str = "http://localhost:8000"
    API_URL: str = "http://localhost:8000"
    YOOKASSA_SHOP_ID: str | None = None
    YOOKASSA_SECRET_KEY: str | None = None
    YOOKASSA_CURRENCY: str = "RUB"
    YOOKASSA_RETURN_PATH: str = "/payments/return"
    YOOKASSA_PRICES: dict[str, float] = Field(default_factory=dict)

    @field_validator("STRIPE_PRICE_IDS", "YOOKASSA_PRICES", mode="before")
    @classmethod
    def parse_mapping_settings(cls, value):
        if value in (None, ""):
            return {}
        if isinstance(value, str):
            return json.loads(value)
        return value


settings = Settings()
