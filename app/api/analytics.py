from fastapi import APIRouter, HTTPException, Query

from app.core.logger import logger
from app.core.schemas import OnChainMetricsOut
from app.services.onchain_service import fetch_onchain_metrics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/onchain",
    response_model=OnChainMetricsOut,
    summary="On-chain Metrics",
    description="Fetch on-chain metrics for a given blockchain network or address.",
)
async def get_onchain_metrics(
    network: str = Query("ethereum", description="Blockchain network, e.g. ethereum, bsc"),
    address: str | None = Query(None, description="Optional wallet or contract address"),
):
    try:
        return await fetch_onchain_metrics(network=network, address=address)
    except Exception as exc:
        logger.error(f"Error fetching on-chain metrics: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch on-chain metrics")
