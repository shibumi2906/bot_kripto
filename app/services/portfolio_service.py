# File: app/services/portfolio_service.py
from typing import List, Dict, Any
from app.core.schemas import PortfolioAsset
from app.services.data_fetcher import fetch_price
from app.core.logger import logger


def calculate_portfolio_value(assets: List[PortfolioAsset]) -> Dict[str, Any]:
    """
    Compute current value of each asset and total portfolio.
    Returns {'assets': [{'symbol', 'amount', 'value_usd'}], 'total_value'}
    """
    results = []
    total = 0.0
    for asset in assets:
        price = None
        try:
            price = await fetch_price(asset.symbol + 'USDT')
        except Exception:
            logger.warning(f"Failed to fetch price for {asset.symbol}")
            continue
        value = asset.amount * price
        results.append({'symbol': asset.symbol, 'amount': asset.amount, 'value_usd': value})
        total += value
    logger.info(f"Calculated portfolio value: {total}")
    return {'assets': results, 'total_value': total}


def suggest_rebalance(current: Dict[str, float], target: Dict[str, float]) -> Dict[str, float]:
    """
    Suggest adjustments: target and current are symbol->weight (0..1).
    Returns diff: positive means buy %, negative means sell %.
    """
    diffs = {}
    for symbol, tgt in target.items():
        cur = current.get(symbol, 0)
        diffs[symbol] = tgt - cur
    logger.debug(f"Rebalance suggestions: {diffs}")
    return diffs
