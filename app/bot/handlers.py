from aiogram import Router, types
from aiogram.filters import Command
from aiogram.filters.command import CommandObject

from app.domain.analysis import DataQualityError
from app.services.analyst import build_report
from app.services.market_sources import SYMBOLS

router = Router()


@router.message(Command("start", "help"))
async def help_command(message: types.Message):
    await message.answer(
        "Crypto Analyst\n"
        "/demo BTCUSDT — offline synthetic example\n"
        "/analyze BTCUSDT — live Binance / OKX / Kraken\n"
        "Supported: BTCUSDT, ETHUSDT, SOLUSDT. Timeframe: 1h.\n"
        "Risk is a transparent heuristic, not a loss probability. "
        "No orders are executed. AI commentary is available through the local CLI."
    )


@router.message(Command("demo", "analyze", "signals"))
async def analyze_command(message: types.Message, command: CommandObject):
    symbol = (command.args or "BTCUSDT").strip().upper()
    if symbol not in SYMBOLS:
        await message.answer("Supported: BTCUSDT, ETHUSDT, SOLUSDT")
        return
    mode = "demo" if command.command.lower() == "demo" else "live"
    await message.answer("Analyzing closed hourly candles...")
    try:
        report = await build_report(symbol=symbol, mode=mode)
        core = report["core"]
        plan = core["trade_plan"]
        text = (
            f"{symbol} | {mode.upper()} | {core['action']}\n"
            f"Reference close: {core['reference_price']:.4f} USDT\n"
            f"Market stress: {core['risk']['market']['score']}/100 "
            f"({core['risk']['market']['level']})\n"
            f"RSI14: {core['indicators']['rsi14']:.2f}\n"
            f"ATR14: {core['indicators']['atr14']:.4f}\n"
            f"Sources: {', '.join(core['sources'])}\n"
            f"Divergence: {core['divergence_pct']:.4f}%\n"
            + "\n".join(core["reasons"])
        )
        if plan:
            text += (f"\nScenario: {plan['meaning']}\n"
                     f"Stop: {plan['stop_loss']:.4f}; target: {plan['target']:.4f}")
        if mode == "demo":
            text += "\nSYNTHETIC FIXTURE — not current market data."
        if report["collection_errors"]:
            text += "\nSome exchanges unavailable; see source coverage."
    except DataQualityError:
        text = "Insufficient fresh, consistent data from at least two exchanges."
    except Exception:
        text = "Analysis unavailable. No synthetic live signal was substituted."
    await message.answer(text)
