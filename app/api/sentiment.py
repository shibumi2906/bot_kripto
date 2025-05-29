# app/api/sentiment.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.core.db import query

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


class SentimentOut(BaseModel):
    timestamp: datetime
    score: float
    mentions: int


@router.get("/", response_model=List[SentimentOut])
async def get_sentiment(
    asset: str = Query(..., description="Символ актива, напр. ETH"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Возвращает последние записи сентимента по активу.
    """
    rows = query(
        """
        SELECT timestamp, score, mentions
          FROM social_sentiment
         WHERE asset = ?
         ORDER BY timestamp DESC
         LIMIT ?
        """,
        (asset, limit),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Данных сентимента не найдено")
    return [
        SentimentOut(
            timestamp=datetime.fromisoformat(r[0]),
            score=r[1],
            mentions=r[2],
        )
        for r in rows
    ]
