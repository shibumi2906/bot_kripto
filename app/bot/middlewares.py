from aiogram import BaseMiddleware
from aiogram.types import Message, Update
from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.logger import logger
from app.core.models import Subscription


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        message: Message | None = event.message
        if not message or not message.text:
            return await handler(event, data)

        command = message.text.split()[0].lstrip("/")
        protected = {"signals", "portfolio", "onchain"}
        if command not in protected:
            return await handler(event, data)

        user_id = str(message.from_user.id)
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Subscription).filter_by(user_id=user_id))
                subscription = result.scalar_one_or_none()
                if subscription and not subscription.is_active:
                    await message.answer("У вас нет активной подписки. Используйте /subscribe")
                    return
            except Exception as exc:
                logger.error(f"Subscription check failed: {exc}")

        return await handler(event, data)
