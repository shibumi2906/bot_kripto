# app/core/config.py

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Основная конфигурация приложения.
    Все секреты и параметры загружаются из файла .env
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Среда: development или production
    ENVIRONMENT: str = Field("development")

    # Подключение к базе данных PostgreSQL (asyncpg)
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://user:password@host:5432/dbname"
    )

    # Redis (для кеша и хранения сессий)
    REDIS_URL: str = Field("redis://localhost:6379/0")

    # Токен вашего Telegram-бота (обязателен)
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot token")

    # Ключ API OpenAI (обязателен)
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")

    # (Опционально) Ключ Etherscan для on-chain аналитики
    ETHERSCAN_API_KEY: str | None = Field(None)

    # Домен вашего сервиса (используется в ссылках)
    DOMAIN: str = Field("https://bot.example.com")

    # Базовый URL вашего FastAPI (для внутренних запросов бота)
    API_URL: str = Field("https://bot.example.com/api")

    # Настройки Stripe
    STRIPE_API_KEY: str | None = Field(None)
    STRIPE_WEBHOOK_SECRET: str | None = Field(None)
    STRIPE_PRICE_IDS: dict[str, str] = Field(default_factory=lambda: {
        "basic": "price_BasicID",
        "pro": "price_ProID",
    })

    # Настройки YooKassa
    YOOKASSA_SHOP_ID: str | None = Field(None)
    YOOKASSA_SECRET_KEY: str | None = Field(None)
    YOOKASSA_PRICES: dict[str, int] = Field(default_factory=lambda: {
        "basic": 499,
        "pro": 999,
    })
    YOOKASSA_CURRENCY: str | None = Field("RUB")
    YOOKASSA_RETURN_PATH: str | None = Field("/success")

# единственный экземпляр настроек
settings = Settings()




