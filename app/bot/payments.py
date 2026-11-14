from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx

from app.core.config import settings
from app.core.logger import logger

router = Router()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message):
    user_id = str(message.from_user.id)
    plan = "basic"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.API_URL}/payments/create-checkout-session",
                json={"user_id": user_id, "plan": plan},
            )
            response.raise_for_status()
            session_id = response.json().get("sessionId")

        if not session_id:
            raise ValueError("Payment session ID was not returned")

        pay_url = f"https://checkout.stripe.com/pay/{session_id}"
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Оплатить подписку", url=pay_url)
        await message.answer(
            "Перейдите по ссылке для оплаты:",
            reply_markup=keyboard.as_markup(),
        )
    except Exception as exc:
        logger.error(f"Failed to create checkout session: {exc}")
        await message.answer("Не удалось создать платежную сессию. Попробуйте позже.")
