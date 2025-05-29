# File: app/bot/__init__.py

from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram import Dispatcher
from aiogram.types import BotCommand

from app.core.config import settings
from app.bot.handlers import register_handlers

# 1) Создаём Bot, указывая parse_mode через DefaultBotProperties
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

# 2) Создаём Dispatcher и регистрируем в нём хендлеры
dp = Dispatcher()
register_handlers(dp)

async def start_bot():
    """
    Запускает бота: устанавливает команды и стартует поллинг.
    """
    # Устанавливаем команды для пользователя
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="signals", description="Получить сигналы"),
        BotCommand(command="portfolio", description="Показать портфель"),
    ])
    # Запуск polling
    await dp.start_polling(bot, skip_updates=True)


