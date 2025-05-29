# app/services/signal_service.py

from typing import List
from app.services.signal_generator import generate_signal
from app.core.db import execute
from app.core.logger import logger

# Список символов, по которым мы генерим сигналы
SYMBOLS: List[str] = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

async def generate_and_store_signals():
    """
    Для каждого символа:
    1) сгенерировать сигнал через GPT
    2) сохранить его в таблицу signals
    """
    for symbol in SYMBOLS:
        try:
            signal = await generate_signal(symbol)
            execute(
                """
                INSERT INTO signals(
                  asset, signal_type, entry, target, stop_loss, confidence, explanation, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    symbol,
                    signal.get("action", "HOLD"),
                    signal.get("entry", 0),
                    signal.get("target", 0),
                    signal.get("stop_loss", 0),
                    signal.get("confidence", 0),
                    signal.get("explanation", ""),
                ),
            )
            logger.info(f"Stored signal for {symbol}: {signal}")
        except Exception as e:
            logger.error(f"Error generating/storing signal for {symbol}: {e}")
