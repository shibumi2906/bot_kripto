import asyncio

import httpx
import pytest

from app.services.demo_data import DEMO_AS_OF, demo_markets
from app.services.market_sources import fetch_source, fetch_quote


@pytest.mark.parametrize("source", ["binance", "okx", "kraken"])
def test_normalizes_provider_schema_and_drops_open_candle(source):
    candle = demo_markets("BTCUSDT")[0].candles[-1]
    start = candle.timestamp * 1000
    fields = list(map(str, (candle.open, candle.high, candle.low,
                           candle.close, candle.volume)))

    def handler(request):
        if source == "binance":
            rows = [[start, *fields], [DEMO_AS_OF * 1000, *fields]]
        elif source == "okx":
            rows = {"code": "0", "data": [
                [str(DEMO_AS_OF * 1000), *fields, "1", "1", "0"],
                [str(start), *fields, "1", "1", "1"],
            ]}
        else:
            row = [candle.timestamp, *fields[:4], "100", fields[4], 5]
            rows = {"error": [], "result": {
                "XBTUSDT": [row, [DEMO_AS_OF, *row[1:]]], "last": DEMO_AS_OF,
            }}
        return httpx.Response(200, json=rows)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_source(client, source, "BTCUSDT", DEMO_AS_OF)

    result = asyncio.run(run())
    assert len(result.candles) == 1
    assert result.candles[0] == candle


def test_provider_application_error_not_treated_as_data():
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"error": ["Unavailable"]}),
        )) as client:
            return await fetch_source(client, "kraken", "BTCUSDT", DEMO_AS_OF)

    with pytest.raises(ValueError):
        asyncio.run(run())


@pytest.mark.parametrize("source", ["binance", "okx", "kraken"])
def test_quote_normalization_and_timestamp_semantics(source, monkeypatch):
    from app.services import market_sources
    monkeypatch.setattr(market_sources.time, "time", lambda: DEMO_AS_OF)

    def handler(request):
        if source == "binance":
            body = {"bidPrice": "100.1", "askPrice": "100.2"}
        elif source == "okx":
            body = {"code": "0", "data": [{
                "bidPx": "100.1", "askPx": "100.2",
                "ts": str((DEMO_AS_OF - 2) * 1000),
            }]}
        else:
            body = {"error": [], "result": {
                "XBTUSDT": {"b": ["100.1"], "a": ["100.2"]},
            }}
        return httpx.Response(200, json=body)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_quote(client, source, "BTCUSDT")

    quote = asyncio.run(run())
    assert quote.bid == 100.1
    assert quote.ask == 100.2
    assert quote.timestamp == DEMO_AS_OF - (2 if source == "okx" else 0)
    assert quote.timestamp_kind == ("exchange" if source == "okx" else "received")


def test_failed_quotes_preserve_history_but_block_trade(monkeypatch):
    from app.services import market_sources
    from dataclasses import replace
    from app.domain.analysis import analyze

    samples = demo_markets("BTCUSDT")

    async def history(client, name, symbol, now):
        return replace(samples[0], source=name, quote=None)

    async def quotes(*args):
        raise httpx.ReadTimeout("provider timed out")

    monkeypatch.setattr(market_sources, "fetch_source", history)
    monkeypatch.setattr(market_sources, "fetch_quote", quotes)
    monkeypatch.setattr(market_sources.time, "time", lambda: DEMO_AS_OF)
    series, failures, now = asyncio.run(market_sources.fetch_markets("BTCUSDT"))
    assert len(series) == 3
    assert len(failures) == 3
    assert all(name.endswith(".quote") for name in failures)
    core = analyze(series, as_of=now, mode="live")
    assert core["action"] == "HOLD"
    assert core["trade_plan"] is None
    assert core["execution"]["quotes"] == {}
