# File: app/services/news_service.py

import httpx
from app.core.config import settings
from app.core.db import execute
from app.core.logger import logger

NEWSAPI_URL = "https://newsapi.org/v2/everything"

async def fetch_and_store_news_api(limit: int = 10):
    """
    Запрашивает топ-статьи по криптовалютам из NewsAPI и сохраняет их в таблицу news.
    """
    params = {
        "q": "cryptocurrency OR bitcoin OR ethereum",
        "pageSize": limit,
        "language": "en",
        "apiKey": settings.NEWSAPI_KEY,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(NEWSAPI_URL, params=params)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])

    for art in articles:
        asset = "UNKNOWN"  # при желании можно парсить из art['title']
        title = art.get("title", "")[:200]
        url = art.get("url", "")
        timestamp = art.get("publishedAt", "")
        sentiment_score = 0.0  # позже можно дополнить анализом

        try:
            execute(
                """
                INSERT INTO news(asset, timestamp, title, url, sentiment_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (asset, timestamp, title, url, sentiment_score),
            )
            logger.info(f"📰 Сохранена новость: {title}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении новости «{title}»: {e}")

