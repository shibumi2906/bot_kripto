"""Public hourly candles, normalized to base asset volume and UTC seconds."""
import asyncio
from dataclasses import replace
import time

import httpx

from app.domain.analysis import Candle, MarketSeries, Quote

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


async def fetch_source(client: httpx.AsyncClient, source: str, symbol: str, now: int):
    base = symbol.removesuffix("USDT")
    if source == "binance":
        response = await client.get(
            "https://data-api.binance.vision/api/v3/klines",
            params={"symbol": symbol, "interval": "1h", "limit": 121},
        )
        response.raise_for_status()
        rows = response.json()
        candles = [Candle(int(r[0]) // 1000, *map(float, r[1:6])) for r in rows]
    elif source == "okx":
        response = await client.get(
            "https://www.okx.com/api/v5/market/candles",
            params={"instId": f"{base}-USDT", "bar": "1H", "limit": 121},
        )
        response.raise_for_status()
        data = response.json()
        if data["code"] != "0":
            raise ValueError("OKX rejected market request")
        candles = [
            Candle(int(r[0]) // 1000, *map(float, r[1:6]))
            for r in data["data"] if r[8] == "1"
        ]
    elif source == "kraken":
        pair = ("XBT" if base == "BTC" else base) + "USDT"
        response = await client.get(
            "https://api.kraken.com/0/public/OHLC",
            params={"pair": pair, "interval": 60},
        )
        response.raise_for_status()
        data = response.json()
        if data["error"]:
            raise ValueError("Kraken rejected market request")
        rows = next(v for k, v in data["result"].items() if k != "last")
        candles = [
            Candle(int(r[0]), *map(float, r[1:5]), float(r[6])) for r in rows[:-1]
        ]
    else:
        raise ValueError("Unknown source")
    return MarketSeries(source, symbol, tuple(sorted(
        (c for c in candles if c.timestamp + 3600 <= now), key=lambda c: c.timestamp,
    )[-120:]))


async def fetch_quote(client: httpx.AsyncClient, source: str, symbol: str) -> Quote:
    base = symbol.removesuffix("USDT")
    if source == "binance":
        response = await client.get(
            "https://data-api.binance.vision/api/v3/ticker/bookTicker",
            params={"symbol": symbol},
        )
        response.raise_for_status()
        data = response.json()
        return Quote(int(time.time()), float(data["bidPrice"]),
                     float(data["askPrice"]), "received")
    if source == "okx":
        response = await client.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": f"{base}-USDT"},
        )
        response.raise_for_status()
        data = response.json()
        if data["code"] != "0":
            raise ValueError("OKX rejected quote request")
        ticker = data["data"][0]
        return Quote(int(ticker["ts"]) // 1000, float(ticker["bidPx"]),
                     float(ticker["askPx"]), "exchange")
    if source == "kraken":
        pair = ("XBT" if base == "BTC" else base) + "USDT"
        response = await client.get(
            "https://api.kraken.com/0/public/Ticker", params={"pair": pair},
        )
        response.raise_for_status()
        data = response.json()
        if data["error"]:
            raise ValueError("Kraken rejected quote request")
        ticker = next(iter(data["result"].values()))
        return Quote(int(time.time()), float(ticker["b"][0]),
                     float(ticker["a"][0]), "received")
    raise ValueError("Unknown quote source")


async def fetch_markets(symbol: str) -> tuple[tuple[MarketSeries, ...], dict, int]:
    if symbol not in SYMBOLS:
        raise ValueError("Unsupported symbol")
    now = int(time.time())
    names = ("binance", "okx", "kraken")
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        results = await asyncio.gather(
            *(fetch_source(client, name, symbol, now) for name in names),
            *(fetch_quote(client, name, symbol) for name in names),
            return_exceptions=True,
        )
    series, failures = [], {}
    for name, result, quote in zip(names, results[:3], results[3:]):
        if isinstance(result, Exception):
            # Do not forward raw HTTP errors or arbitrary provider payloads.
            failures[name] = type(result).__name__
        else:
            if isinstance(quote, Exception):
                failures[f"{name}.quote"] = type(quote).__name__
                quote = None
            series.append(replace(result, quote=quote))
    return tuple(series), failures, int(time.time())
