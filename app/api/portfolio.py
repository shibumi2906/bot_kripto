# File: app/api/portfolio.py
from fastapi import APIRouter
from app.core.schemas import PortfolioOut

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/", response_model=PortfolioOut)
async def get_portfolio():
    """Return current portfolio state."""
    # TODO: implement portfolio retrieval
    return PortfolioOut(assets=[], total_value=0)
