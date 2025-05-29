# File: app/api/payments.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import stripe
from datetime import datetime, timedelta
import sqlite3

from app.core.config import settings
from app.core.logger import logger
from app.core.db import execute

router = APIRouter(prefix="/payments", tags=["payments"])

# Настраиваем ключ Stripe
stripe.api_key = settings.STRIPE_API_KEY
STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET  # из config.py

@router.post("/create-checkout-session")
async def create_checkout_session(user_id: int, plan: str):
    """
    Создать Stripe Checkout сессию для подписки пользователя.
    """
    price_id = settings.STRIPE_PRICE_IDS.get(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Unknown plan")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"user_id": str(user_id), "plan": plan},
            success_url=f"{settings.DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.DOMAIN}/cancel",
        )
        return {"sessionId": session.id}
    except Exception as e:
        logger.error(f"Stripe session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Обработчик вебхуков от Stripe.
    При событии checkout.session.completed обновляем таблицу subscriptions.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        user_id = int(session_obj["metadata"]["user_id"])
        plan = session_obj["metadata"]["plan"]
        # Считаем срок действия подписки (30 дней от now)
        expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

        # Вставляем или обновляем запись в subscriptions
        try:
            execute(
                """
                INSERT INTO subscriptions(
                    telegram_id, provider, status, started_at, expires_at
                ) VALUES (?, ?, ?, datetime('now'), ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    provider=excluded.provider,
                    status=excluded.status,
                    expires_at=excluded.expires_at;
                """,
                (user_id, "stripe", "active", expires_at),
            )
            logger.info(f"Activated subscription for user {user_id} (plan={plan})")
        except sqlite3.Error as e:
            logger.error(f"DB error updating subscriptions: {e}")

    return JSONResponse(status_code=200, content={"received": True})

