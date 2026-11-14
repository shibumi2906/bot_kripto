from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.logger import logger
from app.core.models import PortfolioItem
from app.core.schemas import PortfolioAsset, PortfolioOut
from app.services.portfolio_service import calculate_portfolio_value

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get(
    "/",
    response_model=PortfolioOut,
    summary="Get User Portfolio",
    description="Return current portfolio state for the given user.",
)
async def get_portfolio(
    user_id: UUID | None = Query(None, description="User identifier to fetch portfolio for"),
    db: AsyncSession = Depends(get_db),
):
    if user_id is None:
        return PortfolioOut(assets=[], total_value=0.0)

    try:
        result = await db.execute(select(PortfolioItem).filter_by(user_id=user_id))
        items = result.scalars().all()
        assets = [
            PortfolioAsset(symbol=item.symbol, amount=item.amount)
            for item in items
        ]
        portfolio_data = await calculate_portfolio_value(assets)
        return PortfolioOut(**portfolio_data)
    except Exception as exc:
        logger.error(f"Error retrieving portfolio for user {user_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio",
        )
