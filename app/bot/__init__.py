# File: app/bot/__init__.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings
from app.bot.handlers import router as bot_router
from app.bot.middlewares import SubscriptionMiddleware

# Исправленный конструктор без parse_mode в сигнатуре
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем middleware и router
dp.update.middleware.register(SubscriptionMiddleware())
dp.include_router(bot_router)

async def start_bot():
    """Start polling the Telegram bot."""
    await dp.start_polling(bot)


