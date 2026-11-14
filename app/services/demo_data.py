"""Explicitly synthetic, fixed inputs for reproducible offline demos."""
import math

from app.domain.analysis import Candle, MarketSeries, Quote

DEMO_AS_OF = 1_768_032_000  # fixed hourly boundary, not current market data


def demo_markets(symbol: str) -> tuple[MarketSeries, ...]:
    prices = {"BTCUSDT": 90000, "ETHUSDT": 3000, "SOLUSDT": 150}
    if symbol not in prices:
        raise ValueError("Unsupported symbol")
    result = []
    for name, offset in (("demo-binance", 0), ("demo-okx", .0002),
                         ("demo-kraken", -.0002)):
        candles = []
        for i in range(120):
            price = prices[symbol] * (1 + .0005 * i + .008 * math.sin(i / 3))
            price *= 1 + offset
            candles.append(Candle(
                DEMO_AS_OF - (120 - i) * 3600,
                price * .999, price * 1.004, price * .996, price,
                100 + i % 15,
            ))
        last = candles[-1].close
        result.append(MarketSeries(name, symbol, tuple(candles),
                                   Quote(DEMO_AS_OF, last * .9999, last * 1.0001)))
    return tuple(result)
