# File: app/api/portfolio.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.schemas import PortfolioOut, PortfolioAsset
from app.core.db import get_db
from app.services.portfolio_service import calculate_portfolio_value

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/", response_model=PortfolioOut)
async def get_portfolio(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return current portfolio state for the given user.
    - user_id: строковый идентификатор пользователя (например, Telegram ID или UUID)
    """
    try:
        # Сервис возвращает {'assets': [...], 'total_value': float}
        result = await calculate_portfolio_value(db, user_id)
        # Приводим каждый asset к Pydantic-модели
        assets: List[PortfolioAsset] = [
            PortfolioAsset(**asset_dict) for asset_dict in result["assets"]
        ]
        return PortfolioOut(assets=assets, total_value=result["total_value"])
    except Exception as e:
        # Ловим любые ошибки и возвращаем 500
        raise HTTPException(status_code=500, detail=str(e))

