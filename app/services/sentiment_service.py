# app/services/sentiment_service.py

import httpx
from typing import List, Dict, Any
from app.core.db import execute
from app.core.logger import logger

# Примерный endpoint и ключ для сбора постов — замени на реальный
SENTIMENT_API_URL = "https://api.example.com/sentiment"

async def fetch_and_store_sentiment(limit: int = 20):
    """
    Получаем посты/твиты, считаем тональность и сохраняем.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(SENTIMENT_API_URL, params={"limit": limit})
        resp.raise_for_status()
        data: List[Dict[str, Any]] = resp.json()

    for rec in data:
        asset = rec.get("asset", "UNKNOWN")
        timestamp = rec.get("timestamp")
        score = rec.get("score", 0.0)
        mentions = rec.get("mentions", 0)

        try:
            execute(
                """
                INSERT INTO social_sentiment(asset, timestamp, score, mentions)
                VALUES (?, ?, ?, ?)
                """,
                (asset, timestamp, score, mentions),
            )
        except Exception as e:
            logger.error(f"Failed to insert sentiment for {asset}: {e}")
        else:
            logger.info(f"Stored sentiment for {asset}: score={score}, mentions={mentions}")
