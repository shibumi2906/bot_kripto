# app/services/onchain_service.py

import httpx
from app.core.config import settings
from app.core.db import execute
from app.core.logger import logger

ETHERSCAN_URL = "https://api.etherscan.io/api"

async def fetch_and_store_onchain(symbol: str = "ETH"):
    """
    Запрос к Etherscan: активные адреса и объём tx для токена.
    """
    address_param = symbol  # или конвертация, если надо
    params = {
        "module": "account",
        "action": "txlist",
        "address": settings.ADDRESS_MAPPING.get(symbol, symbol),
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": settings.ETHERSCAN_API_KEY,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(ETHERSCAN_URL, params=params)
        resp.raise_for_status()
        result = resp.json().get("result", [])

    active_addresses = len({tx["from"] for tx in result} | {tx["to"] for tx in result})
    tx_volume = sum(float(tx["value"]) for tx in result) / 1e18  # wei → ETH

    execute(
        """
        INSERT INTO onchain_metrics(asset, timestamp, active_addresses, tx_volume)
        VALUES (?, datetime('now'), ?, ?)
        """,
        (symbol, active_addresses, tx_volume),
    )
    logger.info(f"Stored on-chain for {symbol}: addresses={active_addresses}, volume={tx_volume}")
