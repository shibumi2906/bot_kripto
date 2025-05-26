# File: app/bot/payments.py
from aiogram import Router, types
from aiogram.filters import Command
import httpx
from app.core.config import settings
from app.core.logger import logger

router = Router()

@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message):
    """Send a payment link to the user for subscription."""
    user_id = str(message.from_user.id)
    plan = "basic"  # TODO: allow dynamic plan selection
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.API_URL}/payments/create-checkout-session",
                json={"user_id": user_id, "plan": plan},
                timeout=10
            )
            resp.raise_for_status()
            session = resp.json().get("sessionId")
        pay_url = f"https://checkout.stripe.com/pay/{session}"
        keyboard = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Оплатить подписку", url=pay_url)
        )
        await message.answer("🎟️ Перейдите по ссылке для оплаты:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        await message.answer("❗️ Не удалось создать платежную сессию. Попробуйте позже.")
