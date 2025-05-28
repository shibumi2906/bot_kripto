# bot_polling.py
import asyncio
from app.bot import start_bot   # <-- именно так

if __name__ == "__main__":
    asyncio.run(start_bot())
    print("Bot started")
