from dataclasses import replace
import math

import pytest

from app.domain.analysis import (
    Candle, MarketSeries, Quote, _indicators, analyze,
)
from app.services.demo_data import DEMO_AS_OF, demo_markets
from test_analysis import trend_sources


def evaluate(sources, **kwargs):
    return analyze(sources, as_of=DEMO_AS_OF, mode="live", **kwargs)


@pytest.mark.parametrize("as_of", [math.nan, math.inf, -1, True, "now", 1.5, None])
def test_invalid_analysis_time_rejected(as_of):
    with pytest.raises(ValueError, match="as_of"):
        analyze(demo_markets("BTCUSDT"), as_of=as_of, mode="live")


@pytest.mark.parametrize("timestamp", [math.nan, math.inf, -3600, True, 1.5])
def test_invalid_candle_time_rejected(timestamp):
    sources = demo_markets("BTCUSDT")
    broken = tuple(replace(s, candles=(
        *s.candles[:-1], replace(s.candles[-1], timestamp=timestamp),
    )) for s in sources)
    with pytest.raises(ValueError):
        evaluate(broken)


def test_zero_volume_cannot_create_trade_even_with_fresh_quotes():
    sources = tuple(replace(s, candles=tuple(
        replace(c, volume=0) for c in s.candles
    )) for s in trend_sources(1))
    result = evaluate(sources, balance=1000)
    assert result["action"] == "HOLD"
    assert result["trade_plan"] is None
    assert result["risk"]["data_quality"]["activity"] == "insufficient"


@pytest.mark.parametrize("zero_indices", [[119], list(range(96, 102))])
def test_latest_empty_or_sparse_recent_hours_block_trade(zero_indices):
    sources = tuple(replace(s, candles=tuple(
        replace(c, volume=0) if i in zero_indices else c
        for i, c in enumerate(s.candles)
    )) for s in trend_sources(1))
    assert evaluate(sources)["action"] == "HOLD"


def test_smooth_crash_is_high_stress_despite_near_zero_variance():
    candles = tuple(
        Candle(DEMO_AS_OF - (120 - i) * 3600,
               100 * .97 ** i, 100 * .97 ** i * 1.001,
               100 * .97 ** i * .999, 100 * .97 ** i, 100)
        for i in range(120)
    )
    sources = tuple(MarketSeries(n, "BTCUSDT", candles) for n in ("a", "b", "c"))
    result = evaluate(sources)
    assert result["indicators"]["volatility_24h_pct"] < 1e-8
    assert result["risk"]["market"]["score"] == 100
    assert result["risk"]["market"]["level"] == "high"
    assert result["action"] == "HOLD"
    assert result["risk"]["position"] is None


def test_market_stress_and_source_coverage_are_separate():
    sources = demo_markets("BTCUSDT")
    all_sources = evaluate(sources)
    # All demo sources have proportional prices and identical return histories.
    two_sources = evaluate(sources[:2])
    assert two_sources["risk"]["data_quality"]["history_coverage"] == "reduced"
    assert all_sources["risk"]["data_quality"]["history_coverage"] == "full"
    assert two_sources["risk"]["market"]["score"] == pytest.approx(
        all_sources["risk"]["market"]["score"], abs=1e-8,
    )


@pytest.mark.parametrize("quote", [
    None,
    Quote(DEMO_AS_OF - 31, 109, 109.01),
    Quote(DEMO_AS_OF + 1, 109, 109.01),
    Quote(DEMO_AS_OF, math.nan, 109.01),
    Quote(DEMO_AS_OF, 110, 109),
    Quote(DEMO_AS_OF, 109, 109.01, "invented"),
])
def test_invalid_or_missing_quotes_cannot_create_trade(quote):
    sources = tuple(replace(s, quote=quote) for s in trend_sources(1))
    result = evaluate(sources)
    assert result["action"] == "HOLD"
    assert result["trade_plan"] is None
    assert not result["risk"]["data_quality"]["execution_ready"]


def test_single_quote_is_insufficient_even_with_three_histories():
    sources = trend_sources(1)
    sources = (sources[0], *(replace(s, quote=None) for s in sources[1:]))
    assert evaluate(sources)["action"] == "HOLD"


def test_wide_spread_blocks_directional_scenario():
    sources = tuple(replace(s, quote=Quote(
        DEMO_AS_OF, s.candles[-1].close * .998, s.candles[-1].close * 1.002,
    )) for s in trend_sources(1))
    result = evaluate(sources)
    assert result["execution"]["max_spread_pct"] > .2
    assert result["action"] == "HOLD"


def test_price_moved_since_close_blocks_scenario():
    sources = tuple(replace(s, quote=Quote(
        DEMO_AS_OF, s.candles[-1].close * 1.01, s.candles[-1].close * 1.0101,
    )) for s in trend_sources(1))
    result = evaluate(sources)
    assert result["execution"]["max_entry_drift_pct"] > .5
    assert result["action"] == "HOLD"


def test_entry_uses_current_ask_not_historical_close():
    sources = tuple(replace(s, quote=Quote(
        DEMO_AS_OF, s.candles[-1].close * 1.001,
        s.candles[-1].close * 1.0011,
    )) for s in trend_sources(1))
    result = evaluate(sources, balance=1000, risk_percent=1)
    plan = result["trade_plan"]
    assert result["action"] == "BUY"
    assert plan["entry"] == pytest.approx(sources[0].quote.ask)
    assert plan["entry"] != result["reference_price"]
    assert plan["entry_basis"] == "ask"
    assert plan["position"]["planned_balance_loss_pct"] <= 1.00000001
    assert result["risk"]["position"] == plan["position"]


def test_quote_changes_input_fingerprint():
    sources = trend_sources(1)
    modified = (replace(sources[0], quote=replace(
        sources[0].quote, timestamp=DEMO_AS_OF - 1,
    )), *sources[1:])
    assert evaluate(sources)["input_hash"] != evaluate(modified)["input_hash"]


def history(closes):
    return tuple(Candle(DEMO_AS_OF - (len(closes) - i) * 3600,
                        p, p + 1, p - 1, p, 100)
                 for i, p in enumerate(closes))


def test_arithmetic_reference_values_for_linear_history():
    # Hand-computable: last 20 values 41..60, last 50 values 11..60.
    values = _indicators(history(list(range(1, 61))))
    assert values["sma20"] == 50.5
    assert values["sma50"] == 35.5
    assert values["rsi14"] == 100
    assert values["atr14"] == 2
    assert values["return_24h_pct"] == pytest.approx((60 / 36 - 1) * 100)
    assert values["max_drawdown_24h_pct"] == 0
    assert values["volume_ratio"] == 1
    # Independent population-variance reference, not statistics.pstdev.
    returns = [math.log(i / (i - 1)) for i in range(37, 61)]
    avg = sum(returns) / 24
    expected = math.sqrt(sum((r - avg) ** 2 for r in returns) / 24) * math.sqrt(24) * 100
    assert values["volatility_24h_pct"] == pytest.approx(expected, rel=1e-12)


def test_rsi_and_atr_reference_for_alternating_moves():
    closes = [100]
    for i in range(59):
        closes.append(closes[-1] + (2 if i % 2 == 0 else -1))
    values = _indicators(history(closes))
    # Last 14 intervals: seven gains of 2, seven losses of 1.
    assert values["rsi14"] == pytest.approx(100 * 2 / 3)
    # TR=3 for each +2 move; TR=2 for each -1 move.
    assert values["atr14"] == 2.5


def test_drawdown_and_worst_hour_reference():
    values = _indicators(history([100] * 56 + [110, 99, 105, 90]))
    assert values["max_drawdown_24h_pct"] == pytest.approx(20 / 110 * 100)
    assert values["worst_hour_24h_pct"] == pytest.approx(-15 / 105 * 100)
    assert values["return_24h_pct"] == pytest.approx(-10)


def test_flat_history_rsi_and_volatility_reference():
    values = _indicators(history([100] * 60))
    assert values["rsi14"] == 50
    assert values["volatility_24h_pct"] == 0
    assert values["atr14"] == 2
