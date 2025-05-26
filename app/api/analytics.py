# File: app/api/analytics.py
from fastapi import APIRouter
from app.core.schemas import OnChainMetricsOut

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/onchain", response_model=OnChainMetricsOut)
async def get_onchain_metrics():
    """Fetch on-chain metrics via Etherscan or similar."""
    # TODO: integrate Etherscan API for on-chain metrics
    return OnChainMetricsOut(active_addresses=0, tx_count=0)

