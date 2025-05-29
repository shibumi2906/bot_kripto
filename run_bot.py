# File: run_bot.py

import asyncio
from app.tasks.scheduler import start_scheduler
from app.bot import start_bot

async def main():
    # Запускаем планировщик внутри event loop
    start_scheduler()
    # Затем стартуем бота (он не блокирует loop, т.к. внутри start_polling)
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())

