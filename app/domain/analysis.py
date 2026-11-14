from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from statistics import mean, median, pstdev

HOUR = 3600
ENGINE_VERSION = "technical-v2"
MAX_QUOTE_AGE = 30
MAX_SPREAD_PCT = 0.2
MAX_ENTRY_DRIFT_PCT = 0.5


class DataQualityError(ValueError):
    pass


@dataclass(frozen=True)
class Candle:
    timestamp: int  # UTC opening time, seconds
    open: float
    high: float
    low: float
    close: float
    volume: float  # base asset units


@dataclass(frozen=True)
class Quote:
    timestamp: int
    bid: float
    ask: float
    timestamp_kind: str = "exchange"


@dataclass(frozen=True)
class MarketSeries:
    source: str
    symbol: str
    candles: tuple[Candle, ...]
    quote: Quote | None = None


def _timestamp(value: int) -> bool:
    return type(value) is int and value >= 0


def _number(value: float) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _validate(series: MarketSeries, as_of: int) -> None:
    if len(series.candles) < 60:
        raise DataQualityError("At least 60 closed hourly candles required")
    previous = None
    for candle in series.candles:
        prices = (candle.open, candle.high, candle.low, candle.close)
        if not all(_number(v) and v > 0 for v in prices):
            raise DataQualityError("Prices must be finite and positive")
        if not _number(candle.volume) or candle.volume < 0:
            raise DataQualityError("Invalid volume")
        if candle.low > min(prices) or candle.high < max(prices):
            raise DataQualityError("Invalid OHLC ordering")
        if (not _timestamp(candle.timestamp) or candle.timestamp % HOUR
                or candle.timestamp + HOUR > as_of):
            raise DataQualityError("Unclosed or unaligned candle")
        if previous is not None and candle.timestamp - previous != HOUR:
            raise DataQualityError("Duplicate or missing hourly candles")
        previous = candle.timestamp
    if as_of - (series.candles[-1].timestamp + HOUR) >= HOUR:
        raise DataQualityError("Stale candle history")


def _indicators(candles: tuple[Candle, ...]) -> dict:
    closes = [c.close for c in candles]
    differences = [b - a for a, b in zip(closes[-15:-1], closes[-14:])]
    gain = mean(max(d, 0) for d in differences)
    loss = mean(max(-d, 0) for d in differences)
    rsi = 50.0 if gain == loss == 0 else (
        100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    )
    true_ranges = [
        max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close))
        for p, c in zip(candles[-15:-1], candles[-14:])
    ]
    returns = [math.log(b / a) for a, b in zip(closes[-25:-1], closes[-24:])]
    peak, drawdown = closes[-25], 0.0
    for close in closes[-25:]:
        peak = max(peak, close)
        drawdown = max(drawdown, (peak - close) / peak * 100)
    fast, slow = mean(closes[-20:]), mean(closes[-50:])
    trend = "up" if closes[-1] > fast > slow else (
        "down" if closes[-1] < fast < slow else "mixed"
    )
    return {
        "close": closes[-1], "sma20": fast, "sma50": slow,
        "rsi14": rsi, "atr14": mean(true_ranges),
        "volatility_24h_pct": pstdev(returns) * math.sqrt(24) * 100,
        "return_24h_pct": (closes[-1] / closes[-25] - 1) * 100,
        "max_drawdown_24h_pct": drawdown,
        "worst_hour_24h_pct": min(0.0, min(
            (b / a - 1) * 100 for a, b in zip(closes[-25:-1], closes[-24:])
        )),
        "active_hours_24h": sum(c.volume > 0 for c in candles[-24:]),
        "latest_volume": candles[-1].volume,
        "volume_ratio": candles[-1].volume / mean(c.volume for c in candles[-21:-1])
        if mean(c.volume for c in candles[-21:-1]) > 0 else 0.0,
        "trend": trend,
    }


def _quote_issue(quote: Quote | None, as_of: int) -> str | None:
    if quote is None:
        return "Missing current bid/ask"
    if not _timestamp(quote.timestamp) or not 0 <= as_of - quote.timestamp <= MAX_QUOTE_AGE:
        return "Stale, future or invalid quote timestamp"
    if quote.timestamp_kind not in ("exchange", "received"):
        return "Unknown quote timestamp semantics"
    if not all(_number(v) and v > 0 for v in (quote.bid, quote.ask)):
        return "Invalid bid/ask"
    if quote.bid > quote.ask:
        return "Crossed bid/ask"
    return None


def analyze(
    series: tuple[MarketSeries, ...], *, as_of: int, mode: str,
    balance: float | None = None, risk_percent: float = 0.5,
) -> dict:
    """Same normalized inputs produce byte-for-byte equal JSON-compatible output."""
    if not _timestamp(as_of):
        raise ValueError("as_of must be a nonnegative integer UTC timestamp")
    if mode not in ("demo", "live"):
        raise ValueError("Invalid mode")
    if not _number(risk_percent) or not 0 < risk_percent <= 1:
        raise ValueError("Risk percent must be in (0, 1]")
    if balance is not None and (not _number(balance) or balance <= 0):
        raise ValueError("Balance must be positive and finite")
    if not series:
        raise DataQualityError("No sources")
    if len({s.source for s in series}) != len(series):
        raise DataQualityError("Duplicate source")
    if len({s.symbol for s in series}) != 1:
        raise DataQualityError("Sources must use the same trading pair")
    if series[0].symbol not in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        raise DataQualityError("Unsupported symbol")

    valid, rejected = [], {}
    for source in sorted(series, key=lambda s: s.source):
        try:
            _validate(source, as_of)
            valid.append(source)
        except DataQualityError as exc:
            rejected[source.source] = str(exc)
    if len(valid) < 2:
        raise DataQualityError("At least two fresh independent sources required")

    shared = sorted(set.intersection(*[
        {c.timestamp for c in source.candles} for source in valid
    ]))
    if len(shared) < 60 or as_of - shared[-1] - HOUR >= HOUR:
        raise DataQualityError("Insufficient synchronized history")
    # Each source must have an uninterrupted history over the comparison window.
    shared = shared[-120:]
    if any(b - a != HOUR for a, b in zip(shared, shared[1:])):
        raise DataQualityError("Gap in common history")
    by_source = {}
    for source in valid:
        candles = {c.timestamp: c for c in source.candles}
        by_source[source.source] = _indicators(tuple(candles[t] for t in shared))

    price = median(v["close"] for v in by_source.values())
    divergence = (max(v["close"] for v in by_source.values())
                  - min(v["close"] for v in by_source.values())) / price * 100
    atr = median(v["atr14"] for v in by_source.values())
    atr_pct = atr / price * 100
    vol = median(v["volatility_24h_pct"] for v in by_source.values())
    rsi = median(v["rsi14"] for v in by_source.values())
    trends = {v["trend"] for v in by_source.values()}
    change = median(v["return_24h_pct"] for v in by_source.values())
    drawdown = max(v["max_drawdown_24h_pct"] for v in by_source.values())
    worst_hour = min(v["worst_hour_24h_pct"] for v in by_source.values())
    # Separate market stress from data quality. Maximum prevents calm variance
    # from averaging away a sustained crash. Thresholds are policy, not calibration.
    components = {
        "atr": min(100.0, atr_pct / 5 * 100),
        "volatility": min(100.0, vol / 10 * 100),
        "absolute_return_24h": min(100.0, abs(change) / 10 * 100),
        "drawdown_24h": min(100.0, drawdown / 10 * 100),
        "worst_hour": min(100.0, abs(worst_hour) / 3 * 100),
    }
    score = round(max(components.values()), 2)
    inactive = [
        name for name, values in by_source.items()
        if values["latest_volume"] <= 0 or values["active_hours_24h"] < 20
    ]
    quotes, quote_rejections = {}, {}
    for source in valid:
        issue = _quote_issue(source.quote, as_of)
        if issue:
            quote_rejections[source.source] = issue
        else:
            quotes[source.source] = source.quote
    spread = max(
        ((q.ask - q.bid) / ((q.bid + q.ask) / 2) * 100 for q in quotes.values()),
        default=None,
    )
    mids = [(q.bid + q.ask) / 2 for q in quotes.values()]
    quote_divergence = (max(mids) - min(mids)) / median(mids) * 100 if mids else None
    # Use the worst accepted quote, not a median which could hide one moved book.
    drift = max((abs(v / price - 1) * 100 for q in quotes.values()
                 for v in (q.bid, q.ask)), default=None)
    execution_blocks = []
    if len(quotes) < 2:
        execution_blocks.append("At least two fresh bid/ask sources required")
    if spread is not None and spread > MAX_SPREAD_PCT:
        execution_blocks.append("Bid/ask spread exceeds 0.2%")
    if quote_divergence is not None and quote_divergence > 0.5:
        execution_blocks.append("Current quote divergence exceeds 0.5%")
    if drift is not None and drift > MAX_ENTRY_DRIFT_PCT:
        execution_blocks.append("Current price moved over 0.5% from the analyzed close")
    reasons = []
    action = "HOLD"
    if inactive:
        reasons.append("Insufficient recent trading activity")
    elif execution_blocks:
        reasons.extend(execution_blocks)
    elif divergence > 0.5:
        reasons.append("Cross-exchange divergence exceeds 0.5%")
    elif score >= 60:
        reasons.append("Market stress is elevated; no directional scenario")
    elif trends == {"up"} and 45 <= rsi <= 70:
        action = "BUY"
        reasons.append("All sources agree on an uptrend; RSI is not overbought")
    elif trends == {"down"} and 30 <= rsi <= 55:
        action = "SELL"
        reasons.append("All sources agree on a downtrend; reduce spot exposure")
    else:
        reasons.append("No aligned trend with acceptable RSI")
    if rejected:
        reasons.append("Some supplied sources failed quality checks")
    if len(valid) < 3:
        reasons.append("Reduced source coverage")

    trade = None
    if action != "HOLD" and atr > 0:
        entry_source = (
            max(quotes, key=lambda name: quotes[name].ask) if action == "BUY"
            else min(quotes, key=lambda name: quotes[name].bid)
        )
        entry_quote = quotes[entry_source]
        entry = entry_quote.ask if action == "BUY" else entry_quote.bid
        distance = 2 * atr
        stop = entry - distance if action == "BUY" else entry + distance
        target = entry + 2 * distance if action == "BUY" else entry - 2 * distance
        if min(stop, target) > 0:
            trade = {
                "entry": entry, "entry_source": entry_source,
                "entry_timestamp": entry_quote.timestamp,
                "entry_basis": "ask" if action == "BUY" else "bid",
                "stop_loss": stop, "target": target,
                "reward_risk": 2.0, "stop_distance_pct": distance / entry * 100,
                "meaning": "spot_buy" if action == "BUY" else "reduce_spot_exposure",
                "position": None,
            }
            if balance is not None and action == "BUY":
                quantity = min(balance * risk_percent / 100 / distance, balance / entry)
                trade["position"] = {
                    "balance_usdt": balance, "quantity": quantity,
                    "notional_usdt": quantity * entry,
                    "planned_loss_usdt": quantity * distance,
                    "risk_percent": risk_percent,
                    "planned_balance_loss_pct": quantity * distance / balance * 100,
                    "excludes": "fees, slippage, gaps; stop execution not guaranteed",
                }
        if trade is None:
            action = "HOLD"
            reasons = ["Directional scenario has invalid stop/target levels"]
    payload = {
        "version": ENGINE_VERSION, "as_of": as_of, "mode": mode,
        "balance": balance, "risk_percent": risk_percent,
        "series": [asdict(s) for s in sorted(series, key=lambda s: s.source)],
    }
    digest = sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=True,
    ).encode()).hexdigest()
    return {
        "engine_version": ENGINE_VERSION, "input_hash": digest,
        "mode": mode, "symbol": series[0].symbol, "quote_currency": "USDT",
        "as_of": as_of, "timeframe": "1h", "last_closed_candle": shared[-1],
        "sample_count": len(shared), "sources": by_source,
        "rejected_sources": rejected, "reference_price": price,
        "divergence_pct": divergence,
        "execution": {
            "quotes": {name: asdict(q) for name, q in quotes.items()},
            "rejected_quotes": quote_rejections,
            "max_spread_pct": spread, "quote_divergence_pct": quote_divergence,
            "max_entry_drift_pct": drift, "blocks": execution_blocks,
            "depth_checked": False,
        },
        "indicators": {"rsi14": rsi, "atr14": atr, "atr_pct": atr_pct,
                       "volatility_24h_pct": vol, "return_24h_pct": change,
                       "max_drawdown_24h_pct": drawdown,
                       "worst_hour_24h_pct": worst_hour},
        "risk": {
            "data_quality": {
                "history_coverage": "full" if len(valid) >= 3 else "reduced",
                "quote_source_count": len(quotes),
                "activity": "insufficient" if inactive else "sufficient",
                "inactive_sources": inactive,
                "execution_ready": not execution_blocks and not inactive and divergence <= 0.5,
            },
            "market": {
                "score": score, "aggregation": "maximum",
                "scale": "0..100 heuristic stress; not loss probability or safety",
                "level": "high" if score >= 60 else "elevated" if score >= 30 else "normal",
                "components": components,
            },
            "position": trade["position"] if trade else None,
        },
        "action": action, "reasons": reasons, "trade_plan": trade,
    }
