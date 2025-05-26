# File: app/tasks/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.signal_generator import generate_signal
from app.core.logger import logger
import asyncio

scheduler = AsyncIOScheduler()

async def job_signal_generation():
    symbol = "BTCUSDT"
    try:
        signal = await generate_signal(symbol)
        logger.info(f"Scheduled signal for {symbol}: {signal}")
    except Exception as e:
        logger.error(f"Error in scheduled signal generation: {e}")


def start_scheduler():
    """
    Configure and start the AsyncIO scheduler with defined jobs.
    """
    scheduler.add_job(job_signal_generation, 'interval', minutes=5)
    scheduler.start()
    logger.info("Scheduler started with 5-minute interval for signal generation")

# Optional: You may hook start_scheduler() into FastAPI on_startup event in main.py
