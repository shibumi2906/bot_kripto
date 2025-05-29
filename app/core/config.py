# File: app/core/config.py

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    ENVIRONMENT: str = Field("development", description="development|production")
    DB_PATH: str = Field("./bot.db", description="Путь до SQLite-файла базы")
    REDIS_URL: str = Field("redis://localhost:6379/0", description="URL Redis")

    TELEGRAM_BOT_TOKEN: str = Field(..., description="Токен Telegram-бота")
    OPENAI_API_KEY: str = Field(..., description="API ключ OpenAI")

    # Etherscan
    ETHERSCAN_API_KEY: str = Field(..., description="API ключ Etherscan для on-chain метрик")

    # Stripe
    STRIPE_API_KEY: str = Field(..., description="Секретный ключ Stripe")
    STRIPE_WEBHOOK_SECRET: str = Field(..., description="Секрет вебхуков Stripe")
    STRIPE_PRICE_IDS: dict[str, str] = Field(
        ..., description="JSON с mapping price IDs для планов"
    )

    # YooKassa
    YOOKASSA_SHOP_ID: str = Field(..., description="Shop ID YooKassa")
    YOOKASSA_SECRET_KEY: str = Field(..., description="Secret key YooKassa")
    YOOKASSA_PRICES: dict[str, int] = Field(..., description="JSON с ценами в руб.")
    YOOKASSA_CURRENCY: str = Field("RUB", description="Валюта для YooKassa")
    YOOKASSA_RETURN_PATH: str = Field("/success", description="Путь возврата после оплаты")

    # JWT
    JWT_SECRET_KEY: str = Field(..., description="Секрет для подписи JWT")

    # URLs
    DOMAIN: str = Field(..., description="Домен сервиса (для ссылок)")
    API_URL: str = Field(..., description="URL FastAPI (для webhook'ов бота)")

    CRYPTOCONTROL_API_KEY: str = Field(..., description="API ключ для CryptoControl")

    # Новый ключ для NewsAPI.org
    NEWSAPI_KEY: str = Field(..., description="API ключ для NewsAPI.org")
    # Telegram

# Единственный экземпляр настроек
settings = Settings()








