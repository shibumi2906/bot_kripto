# File: app/bot/handlers.py
from aiogram import Router, types
from aiogram.filters import Command
from app.services.signal_generator import generate_signal
from app.services.portfolio_service import calculate_portfolio_value
# from app.services.onchain_service import fetch_onchain_metrics  # implement when ready
from app.core.logger import logger

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Welcome message and available commands."""
    text = (
        "👋 Привет! Я Crypto Signals Bot. Доступные команды:\n"
        "/signals - получить торговый сигнал\n"
        "/portfolio - текущее состояние портфеля\n"
        "/onchain - on-chain метрики\n"
        "/subscribe - оформить подписку\n"
        "/help - показать это сообщение"
    )
    await message.answer(text)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)

@router.message(Command("signals"))
async def cmd_signals(message: types.Message):
    """Generate and send a trading signal."""
    await message.answer("🔄 Генерирую сигнал...")
    try:
        signal = await generate_signal()
        text = (
            f"🎯 Сигнал: {signal['action']}\n"
            f"Entry: {signal['entry']}\n"
            f"Target: {signal['target']}\n"
            f"Stop-loss: {signal['stop_loss']}\n"
            f"Confidence: {signal['confidence']:.2f}"
        )
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        text = "❗️ Не удалось сгенерировать сигнал. Попробуйте позже."
    await message.answer(text)

@router.message(Command("portfolio"))
async def cmd_portfolio(message: types.Message):
    """Compute and send portfolio value."""
    # TODO: replace stub with user-specific assets
    assets = []  # example: [{'symbol': 'BTC', 'amount': 0.5}]
    try:
        result = calculate_portfolio_value(assets)
        lines = [f"{a['symbol']}: {a['amount']} ({a['value_usd']:.2f} USD)" for a in result['assets']]
        lines.append(f"💰 Общая стоимость: {result['total_value']:.2f} USD")
        text = "\n".join(lines) if lines else "Портфель пуст или не найдено активов."
    except Exception as e:
        logger.error(f"Error calculating portfolio: {e}")
        text = "❗️ Не удалось получить состояние портфеля."
    await message.answer(text)

@router.message(Command("onchain"))
async def cmd_onchain(message: types.Message):
    """Fetch and send on-chain metrics."""
    await message.answer("🔄 Получаю on-chain метрики...")
    try:
        from app.services.onchain_service import fetch_onchain_metrics
        metrics = await fetch_onchain_metrics()
        text = (
            f"🏦 Активные адреса: {metrics.active_addresses}\n"
            f"📊 Кол-во транзакций: {metrics.tx_count}"
        )
    except Exception as e:
        logger.error(f"Error fetching onchain metrics: {e}")
        text = "❗️ Не удалось получить on-chain метрики."
    await message.answer(text)
