# File: app/services/backtester.py
from typing import List, Dict, Any
import pandas as pd
from app.core.logger import logger


def backtest_signal_history(prices: List[float], signals: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Simple backtester: apply signals to price series and compute metrics.
    prices: list of historical prices aligned with signals
    signals: list of dicts with keys ['action','entry','target','stop_loss']
    Returns metrics: {'profit': x, 'trades': n, 'win_rate': y}
    """
    df = pd.DataFrame({'price': prices, 'signal': [s['action'] for s in signals]})
    profit = 0.0
    wins = 0
    trades = 0

    for s in signals:
        entry = s['entry']
        target = s['target']
        stop = s['stop_loss']
        # find index of entry in prices
        # assume entry timestamp aligned; here simplified: use first price equal or above entry
        try:
            price_list = df['price'].tolist()
            idx = min(i for i,p in enumerate(price_list) if p>=entry)
        except Exception:
            continue
        # simulate exit
        period = price_list[idx:]
        exit_price = None
        for p in period:
            if p>=target:
                exit_price = target
                wins +=1
                break
            if p<=stop:
                exit_price = stop
                break
        if exit_price is None:
            exit_price = period[-1]
        profit += (exit_price - entry) if s['action']=='BUY' else (entry - exit_price)
        trades +=1
    win_rate = wins / trades if trades>0 else 0
    logger.info(f"Backtest completed: profit={profit}, trades={trades}, win_rate={win_rate}")
    return {'profit': profit, 'trades': trades, 'win_rate': win_rate}
