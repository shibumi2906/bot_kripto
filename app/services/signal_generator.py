# File: app/services/signal_generator.py
import json
import openai
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logger import logger
from app.services.data_fetcher import fetch_price

openai.api_key = settings.OPENAI_API_KEY

PROMPT_TEMPLATE = """
You are a crypto trading analyst. Latest data for {symbol}:
{data}

Based on this, output JSON:
{{
  "action": "BUY"|"SELL"|"HOLD",
  "entry": <price>,
  "target": <price>,
  "stop_loss": <price>,
  "confidence": <0.0-1.0>
}}
"""

async def generate_signal(symbol: str = "BTCUSDT", lookback: int = 5) -> Dict[str, Any]:
    """Fetch recent prices, build prompt, call GPT-4o, and parse signal."""
    # Gather latest prices
    data = []
    for _ in range(lookback):
        price = await fetch_price(symbol)
        data.append({"price": price})
    prompt = PROMPT_TEMPLATE.format(symbol=symbol, data=json.dumps(data, indent=2))

    logger.info(f"Requesting signal for {symbol}")
    resp = await openai.ChatCompletion.acreate(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional crypto analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=150
    )
    text = resp.choices[0].message.content
    logger.debug(f"Raw signal response: {text}")

    # Parse JSON
    try:
        signal = json.loads(text)
    except Exception as e:
        logger.error(f"Failed to parse signal JSON: {e}")
        raise
    return signal
