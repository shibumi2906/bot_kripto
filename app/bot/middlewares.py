# File: app/bot/middlewares.py
from aiogram import BaseMiddleware
from aiogram.types import Update, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import AsyncSessionLocal
from app.core.models import Subscription
from app.core.logger import logger

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        """
        Block commands requiring subscription if user has no active subscription.
        """
        message: Message = event.message
        if not message or not message.text:
            return await handler(event, data)

        command = message.text.split()[0].lstrip("/")
        protected = ("signals", "portfolio", "onchain")
        if command in protected:
            user_id = str(message.from_user.id)
            async with AsyncSessionLocal() as session:
                try:
                    result = await session.execute(
                        select(Subscription).filter_by(user_id=user_id)
                    )
                    sub = result.scalar_one_or_none()
                    if not sub or not sub.is_active:
                        await message.answer(
                            "⛔ У вас нет активной подписки. Используйте /subscribe"
                        )
                        return  # skip handler
                except Exception as e:
                    logger.error(f"Subscription check failed: {e}")
                    # allow command on error
        return await handler(event, data)
