# File: app/bot/handlers.py

from aiogram import Dispatcher, types
from aiogram.filters import Command
from app.core.db import query
from app.core.config import settings

def register_handlers(dp: Dispatcher) -> None:
    dp.message.register(cmd_start,       Command(commands=["start"]))
    dp.message.register(cmd_help,        Command(commands=["help"]))
    dp.message.register(cmd_signals,     Command(commands=["signals"]))
    dp.message.register(cmd_history,     Command(commands=["history"]))
    dp.message.register(cmd_portfolio,   Command(commands=["portfolio"]))
    dp.message.register(cmd_onchain,     Command(commands=["onchain"]))
    dp.message.register(cmd_subscribe,   Command(commands=["subscribe"]))


async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я Crypto Signals Bot. Доступные команды:\n"
        "/signals   — получить торговый сигнал\n"
        "/portfolio — текущее состояние портфеля\n"
        "/onchain   — on-chain метрики (по активу)\n"
        "/subscribe — оформить подписку\n"
        "/help      — показать это сообщение"
    )

async def cmd_help(message: types.Message):
    # просто дублируем /start
    await cmd_start(message)


async def cmd_signals(message: types.Message):
    rows = query(
        "SELECT asset, signal_type, entry, target, stop_loss, confidence, explanation, created_at "
        "FROM signals ORDER BY created_at DESC LIMIT ?",
        (5,),
    )
    if not rows:
        await message.answer("Пока нет сигналов.")
        return
    parts = []
    for asset, action, entry, target, stop_loss, conf, expl, created in rows:
        parts.append(
            f"<b>{asset}</b> — {action.upper()} @ {entry}\n"
            f"TP: {target}, SL: {stop_loss}\n"
            f"Conf: {conf*100:.1f}%\n"
            f"{expl}\n"
            f"<i>{created}</i>"
        )
    await message.answer("\n\n".join(parts), parse_mode="HTML")


async def cmd_history(message: types.Message):
    rows = query(
        "SELECT asset, signal_type, entry, target, stop_loss, confidence, created_at "
        "FROM signals ORDER BY created_at DESC LIMIT ?",
        (10,),
    )
    if not rows:
        await message.answer("История сигналов пуста.")
        return
    lines = [f"{r[7]} | {r[0]} {r[1].upper()} @ {r[2]} (TP {r[3]}, SL {r[4]})" for r in rows]
    await message.answer("📜 История сигналов:\n" + "\n".join(lines))


async def cmd_portfolio(message: types.Message):
    user_id = message.from_user.id
    rows = query("SELECT asset, amount FROM portfolio WHERE telegram_id = ?", (user_id,))
    if not rows:
        await message.answer("Ваш портфель пуст.")
        return
    lines = [f"{asset}: {amount}" for asset, amount in rows]
    await message.answer("💼 Ваш портфель:\n" + "\n".join(lines))


async def cmd_onchain(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        # Экранируем угловые скобки, чтобы HTML-парсер не ругался
        await message.answer(
            "Использование: /onchain &lt;symbol&gt;\n"
            "Пример: /onchain BTC",
            parse_mode="HTML"
        )
        return

    symbol = parts[1].upper()
    rows = query(
        "SELECT active_addresses, tx_volume FROM onchain_metrics "
        "WHERE asset = ? ORDER BY timestamp DESC LIMIT 1",
        (symbol,),
    )
    if not rows:
        await message.answer(f"Нет on-chain метрик для {symbol}.")
        return

    active, volume = rows[0]
    await message.answer(
        f"📊 On-chain метрики для <b>{symbol}</b>:\n"
        f"Активных адресов: {active}\n"
        f"Объем tx (посл.): {volume}",
        parse_mode="HTML",
    )



async def cmd_subscribe(message: types.Message):
    user_id = message.from_user.id
    # Формируем ссылку на ваш эндпоинт создания Stripe-сессии
    link = (
        f"{settings.API_URL}/payments/create-checkout-session"
        f"?user_id={user_id}&plan=basic"
    )
    await message.answer(
        f"🔑 Оформить подписку можно по ссылке:\n{link}\n"
        "(после оплаты вы получите доступ к премиум-сигналам)"
    )

