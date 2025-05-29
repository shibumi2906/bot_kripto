# app/api/news.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.core.db import query

router = APIRouter(prefix="/news", tags=["news"])


class NewsItem(BaseModel):
    id: int
    asset: str
    title: str
    url: str
    timestamp: datetime
    sentiment_score: float


@router.get("/", response_model=List[NewsItem])
async def get_news(
    asset: str = Query(..., description="Cимвол крипто-актива, напр. BTC"),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Возвращает последние новости по активу из таблицы news.
    """
    rows = query(
        """
        SELECT id, asset, title, url, timestamp, sentiment_score
          FROM news
         WHERE asset = ?
         ORDER BY timestamp DESC
         LIMIT ?
        """,
        (asset, limit),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Новости не найдены")
    return [
        NewsItem(
            id=r[0],
            asset=r[1],
            title=r[2],
            url=r[3],
            timestamp=datetime.fromisoformat(r[4]),
            sentiment_score=r[5],
        )
        for r in rows
    ]
