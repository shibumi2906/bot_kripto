import asyncio
from dataclasses import replace
import json
import math

import pytest

from app.domain.analysis import Candle, DataQualityError, MarketSeries, Quote, analyze
from app.services.demo_data import DEMO_AS_OF, demo_markets


def run(series=None, **kwargs):
    return analyze(series or demo_markets("BTCUSDT"), as_of=DEMO_AS_OF,
                   mode="demo", **kwargs)


def test_reproducible_and_order_independent():
    sources = demo_markets("BTCUSDT")
    assert run(sources) == run(tuple(reversed(sources)))
    assert len(run(sources)["input_hash"]) == 64


def test_input_hash_changes_with_policy_input():
    assert run()["input_hash"] != run(risk_percent=1)["input_hash"]


def test_hold_has_no_trade_plan_or_invented_confidence():
    result = run()
    assert result["action"] == "HOLD"
    assert result["trade_plan"] is None
    assert "confidence" not in result


def test_one_source_is_insufficient():
    with pytest.raises(DataQualityError):
        run(demo_markets("BTCUSDT")[:1])


@pytest.mark.parametrize("defect", ["stale", "nan", "negative", "unclosed", "gap"])
def test_rejects_bad_sources_but_keeps_healthy_quorum(defect):
    sources = list(demo_markets("BTCUSDT"))
    candles = list(sources[0].candles)
    if defect == "stale":
        candles = [replace(c, timestamp=c.timestamp - 7200) for c in candles]
    elif defect == "nan":
        candles[-1] = replace(candles[-1], close=math.nan)
    elif defect == "negative":
        candles[-1] = replace(candles[-1], low=-1)
    elif defect == "unclosed":
        candles[-1] = replace(candles[-1], timestamp=DEMO_AS_OF)
    else:
        candles.pop(10)
    sources[0] = replace(sources[0], candles=tuple(candles))
    result = run(tuple(sources))
    assert sources[0].source in result["rejected_sources"]
    assert len(result["sources"]) == 2
    json.dumps(result, allow_nan=False)


def test_divergent_prices_force_hold():
    sources = list(demo_markets("BTCUSDT"))
    sources[0] = replace(sources[0], candles=tuple(
        replace(c, open=c.open * 1.05, high=c.high * 1.05,
                low=c.low * 1.05, close=c.close * 1.05)
        for c in sources[0].candles
    ))
    assert run(tuple(sources))["action"] == "HOLD"
    assert run(tuple(sources))["divergence_pct"] > .5


def test_mixed_pairs_rejected():
    sources = demo_markets("BTCUSDT")[:2] + demo_markets("ETHUSDT")[2:]
    with pytest.raises(DataQualityError):
        run(sources)


def trend_sources(direction):
    # Trend with frequent small pullbacks: RSI remains below overbought threshold.
    sources = []
    price = 100.0
    candles = []
    for i in range(120):
        price += direction * (.4 if i % 2 else -.25)
        candles.append(Candle(DEMO_AS_OF - (120 - i) * 3600,
                              price, price + .4, price - .4, price, 100))
    for name in ("a", "b", "c"):
        sources.append(MarketSeries(name, "BTCUSDT", tuple(candles),
                                    Quote(DEMO_AS_OF, price * .9999, price * 1.0001)))
    return tuple(sources)


def test_buy_risk_sizing_is_capped_by_balance():
    result = run(trend_sources(1), balance=1000, risk_percent=1)
    assert result["action"] == "BUY"
    plan = result["trade_plan"]
    assert plan["stop_loss"] < plan["entry"] < plan["target"]
    assert plan["position"]["notional_usdt"] <= 1000
    assert plan["position"]["planned_loss_usdt"] <= 10.000001


def test_sell_is_spot_reduction_not_short_position():
    result = run(trend_sources(-1), balance=1000)
    assert result["action"] == "SELL"
    assert result["trade_plan"]["meaning"] == "reduce_spot_exposure"
    assert result["trade_plan"]["position"] is None


def test_ai_cannot_mutate_core_report(monkeypatch):
    from app.services import analyst

    baseline = asyncio.run(analyst.build_report())

    async def malicious_commentary(core):
        core["action"] = "BUY"
        core["risk"]["market"]["score"] = 0
        return {"status": "ok", "text": "Ignore the original action"}

    monkeypatch.setattr(analyst, "explain_report", malicious_commentary)
    result = asyncio.run(analyst.build_report(explain=True))
    assert result["core"] == baseline["core"]


def test_disabled_ai_does_not_send_request(monkeypatch):
    from app.core.config import settings
    from app.services.signal_generator import explain_report
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    assert asyncio.run(explain_report(run()))["status"] == "disabled"
