from typing import Any

from app.core.logger import logger
from app.core.schemas import PortfolioAsset
from app.services.data_fetcher import fetch_price


async def calculate_portfolio_value(assets: list[PortfolioAsset]) -> dict[str, Any]:
    results = []
    total = 0.0

    for asset in assets:
        try:
            price = await fetch_price(f"{asset.symbol.upper()}USDT")
        except Exception as exc:
            logger.warning(f"Failed to fetch price for {asset.symbol}: {exc}")
            price = 0.0

        value = asset.amount * price
        results.append(
            {
                "symbol": asset.symbol.upper(),
                "amount": asset.amount,
                "value_usd": value,
            }
        )
        total += value

    logger.info(f"Calculated portfolio value: {total}")
    return {"assets": results, "total_value": total}


def suggest_rebalance(current: dict[str, float], target: dict[str, float]) -> dict[str, float]:
    diffs = {}
    for symbol, target_weight in target.items():
        current_weight = current.get(symbol, 0.0)
        diffs[symbol] = target_weight - current_weight

    logger.debug(f"Rebalance suggestions: {diffs}")
    return diffs
