import pytest
from app.services.data_fetcher import fetch_ohlcv

@pytest.mark.asyncio
async def test_fetch_ohlcv_returns_expected_structure():
    # забираем 5 последних баров
    bars = await fetch_ohlcv("BTCUSDT", interval="1m", limit=5)
    assert isinstance(bars, list)
    assert len(bars) == 5

    # проверяем, что в каждом баре есть нужные поля
    for bar in bars:
        assert set(bar.keys()) >= {"open_time", "open", "high", "low", "close", "volume", "close_time"}
