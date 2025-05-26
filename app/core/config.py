# File: app/core/config.py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    ETHERSCAN_API_KEY: str = Field(None, env="ETHERSCAN_API_KEY")
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    STRIPE_API_KEY: str = Field(None, env="STRIPE_API_KEY")

    class Config:
        case_sensitive = True

settings = Settings()
