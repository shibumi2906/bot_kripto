# File: app/api/portfolio.py

from fastapi import APIRouter, HTTPException, Query
from typing import List

from app.core.db import query, execute
from app.core.schemas import PortfolioAsset, PortfolioOut

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/", response_model=PortfolioOut)
async def get_portfolio(
    user_id: int = Query(..., description="Telegram ID пользователя"),
):
    """
    Возвращает текущие активы портфеля пользователя и общую стоимость.
    """
    rows: List[tuple] = query(
        "SELECT asset, amount FROM portfolio WHERE telegram_id = ?",
        (user_id,),
    )

    assets: List[PortfolioAsset] = []
    total_value: float = 0.0

    for asset, amount in rows:
        # TODO: здесь можно вызвать сервис котировок для реальной стоимости
        value_usd = 0.0
        assets.append(PortfolioAsset(symbol=asset, amount=amount, value_usd=value_usd))
        total_value += value_usd

    return PortfolioOut(assets=assets, total_value=total_value)


@router.post("/add", response_model=PortfolioAsset)
async def add_asset(
    user_id: int = Query(..., description="Telegram ID пользователя"),
    symbol: str = Query(..., description="Символ актива, например BTC"),
    amount: float = Query(..., gt=0, description="Количество актива"),
):
    """
    Добавляет или увеличивает количество актива в портфеле.
    """
    execute(
        """
        INSERT INTO portfolio (telegram_id, asset, amount)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id, asset) DO UPDATE SET
          amount = amount + excluded.amount
        """,
        (user_id, symbol, amount),
    )

    row = query(
        "SELECT asset, amount FROM portfolio WHERE telegram_id = ? AND asset = ?",
        (user_id, symbol),
    )
    if not row:
        raise HTTPException(status_code=500, detail="Не удалось добавить актив в портфель")

    asset, updated_amount = row[0]
    # TODO: посчитать реальную стоимость через внешний сервис
    return PortfolioAsset(symbol=asset, amount=updated_amount, value_usd=0.0)


@router.post("/remove", response_model=dict)
async def remove_asset(
    user_id: int = Query(..., description="Telegram ID пользователя"),
    symbol: str = Query(..., description="Символ актива для удаления"),
):
    """
    Удаляет заданный актив из портфеля пользователя.
    """
    execute(
        "DELETE FROM portfolio WHERE telegram_id = ? AND asset = ?",
        (user_id, symbol),
    )
    return {"status": "deleted", "asset": symbol}




