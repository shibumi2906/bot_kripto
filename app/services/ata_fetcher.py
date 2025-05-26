# File: app/services/data_fetcher.py
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logger import logger

BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_DEPTH_URL = "https://api.binance.com/api/v3/depth"
COINCAP_ASSETS_URL = "https://api.coincap.io/v2/assets"

async def fetch_binance_price(symbol: str = "BTCUSDT") -> float:
    """Fetch current price from Binance public REST API."""
    params = {"symbol": symbol}
    async with httpx.AsyncClient() as client:
        resp = await client.get(BINANCE_PRICE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    price = float(data.get("price", 0))
    logger.debug(f"Binance price for {symbol}: {price}")
    return price

async def fetch_coincap_price(asset: str = "bitcoin") -> float:
    """Fetch current price from CoinCap public REST API."""
    url = f"{COINCAP_ASSETS_URL}/{asset}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    price = float(data.get("priceUsd", 0))
    logger.debug(f"CoinCap price for {asset}: {price}")
    return price

async def fetch_price(symbol: str = "BTCUSDT", fallback: bool = True) -> float:
    """Try Binance first, optionally fallback to CoinCap on error."""
    try:
        return await fetch_binance_price(symbol)
    except Exception as e:
        logger.warning(f"Binance fetch failed: {e}")
        if fallback:
            # map symbol to CoinCap asset id
            asset = symbol[:-4].lower()  # e.g., BTCUSDT -> btc
            return await fetch_coincap_price(asset)
        raise

async def fetch_order_book(symbol: str = "BTCUSDT", limit: int = 50) -> Dict[str, Any]:
    """Fetch order book (depth) from Binance."""
    params = {"symbol": symbol, "limit": limit}
    async with httpx.AsyncClient() as client:
        resp = await client.get(BINANCE_DEPTH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    logger.debug(f"Fetched order book for {symbol}")
    return {"bids": data.get("bids", []), "asks": data.get("asks", [])}
