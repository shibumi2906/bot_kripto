# File: app/api/analytics.py

from fastapi import APIRouter, HTTPException, Query
from app.core.db import query
from app.core.schemas import OnChainMetricsOut

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/onchain", response_model=OnChainMetricsOut)
async def get_onchain_metrics(
    asset: str = Query(..., description="Символ крипто-актива, например BTC")
):
    """
    Вернуть свежие on-chain метрики для заданного актива из таблицы onchain_metrics.
    """
    rows = query(
        """
        SELECT active_addresses, tx_volume
          FROM onchain_metrics
         WHERE asset = ?
         ORDER BY timestamp DESC
         LIMIT 1
        """,
        (asset,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Метрики не найдены для актива")
    active_addresses, tx_volume = rows[0]
    # В Pydantic-схеме поле называется tx_count, поэтому приводим tx_volume к целому
    return OnChainMetricsOut(active_addresses=active_addresses, tx_count=int(tx_volume))


