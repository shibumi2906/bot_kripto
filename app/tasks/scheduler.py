# File: app/tasks/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.signal_service import generate_and_store_signals
from app.services.news_service import fetch_and_store_news_api
from app.services.sentiment_service import fetch_and_store_sentiment
from app.services.onchain_service import fetch_and_store_onchain
from app.core.logger import logger

# Создаём планировщик, привязанный к текущему asyncio-loop
scheduler = AsyncIOScheduler(timezone="UTC")

def start_scheduler():
    """
    Регистрируем и запускаем фоновые задачи.
    """
    # Генерация сигналов каждые 5 минут
    scheduler.add_job(
        generate_and_store_signals,
        trigger="interval",
        minutes=5,
        id="signals",
        replace_existing=True
    )

    # Сбор новостей через NewsAPI каждые 30 минут
    scheduler.add_job(
        fetch_and_store_news_api,
        trigger="interval",
        minutes=30,
        id="news_api",
        args=[20],  # передаём limit=20
        replace_existing=True
    )

    # Сбор сентимента каждые 15 минут
    scheduler.add_job(
        fetch_and_store_sentiment,
        trigger="interval",
        minutes=15,
        id="sentiment",
        args=[50],  # limit=50
        replace_existing=True
    )

    # On-chain метрики по каждому активу каждый час
    for sym in ["BTC", "ETH", "BNB"]:
        scheduler.add_job(
            fetch_and_store_onchain,
            trigger="cron",
            hour="*",
            id=f"onchain_{sym}",
            args=[sym],
            replace_existing=True
        )

    scheduler.start()
    logger.info("Scheduler started with jobs: signals, news_api, sentiment, onchain")

