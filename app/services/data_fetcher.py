# File: app/services/data_fetcher.py
from typing import Any

import httpx

from app.core.logger import logger

BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_DEPTH_URL = "https://api.binance.com/api/v3/depth"
COINCAP_ASSETS_URL = "https://api.coincap.io/v2/assets"
DEFAULT_TIMEOUT = httpx.Timeout(10.0)

COINCAP_SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binance-coin",
}


async def fetch_binance_price(symbol: str = "BTCUSDT") -> float:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(BINANCE_PRICE_URL, params={"symbol": symbol})
        response.raise_for_status()
        data = response.json()

    price = float(data["price"])
    logger.debug(f"Binance price for {symbol}: {price}")
    return price


async def fetch_coincap_price(asset: str = "bitcoin") -> float:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(f"{COINCAP_ASSETS_URL}/{asset}")
        response.raise_for_status()
        data = response.json().get("data", {})

    price = float(data["priceUsd"])
    logger.debug(f"CoinCap price for {asset}: {price}")
    return price


async def fetch_price(symbol: str = "BTCUSDT", fallback: bool = True) -> float:
    try:
        return await fetch_binance_price(symbol)
    except Exception as exc:
        logger.warning(f"Binance fetch failed for {symbol}: {exc}")
        if not fallback:
            raise

    base_asset = symbol.removesuffix("USDT").upper()
    coincap_asset = COINCAP_SYMBOL_MAP.get(base_asset, base_asset.lower())
    return await fetch_coincap_price(coincap_asset)


async def fetch_order_book(symbol: str = "BTCUSDT", limit: int = 50) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(BINANCE_DEPTH_URL, params={"symbol": symbol, "limit": limit})
        response.raise_for_status()
        data = response.json()

    logger.debug(f"Fetched order book for {symbol}")
    return {"bids": data.get("bids", []), "asks": data.get("asks", [])}
