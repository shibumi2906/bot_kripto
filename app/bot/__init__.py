# File: app/bot/__init__.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.core.config import settings
from app.bot.handlers import router as bot_router
from app.bot.middlewares import SubscriptionMiddleware

# Initialize bot and dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Register middleware and router
dp.update.middleware.register(SubscriptionMiddleware())
dp.include_router(bot_router)

async def start_bot():
    """Start polling the Telegram bot."""
    await dp.start_polling(bot)

# Optionally, you can call asyncio.create_task(start_bot()) in FastAPI on_startup
