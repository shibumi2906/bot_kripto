import asyncio
from datetime import datetime, timedelta
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.logger import logger
from app.core.models import Subscription
from app.core.schemas import CheckoutSessionRequest

router = APIRouter(prefix="/payments", tags=["payments"])


def stripe_is_configured() -> bool:
    return bool(settings.STRIPE_API_KEY and settings.STRIPE_PRICE_IDS)


@router.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutSessionRequest):
    if not stripe_is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    price_id = settings.STRIPE_PRICE_IDS.get(payload.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Unknown plan")

    stripe.api_key = settings.STRIPE_API_KEY
    try:
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"user_id": payload.user_id, "plan": payload.plan},
            success_url=settings.DOMAIN + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.DOMAIN + "/cancel",
        )
        return {"sessionId": session.id}
    except Exception as exc:
        logger.error(f"Stripe session creation failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.STRIPE_API_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured")

    stripe.api_key = settings.STRIPE_API_KEY
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as exc:
        logger.error(f"Invalid Stripe payload: {exc}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as exc:
        logger.error(f"Invalid Stripe signature: {exc}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        user_id = session_obj["metadata"].get("user_id")
        expires_at = datetime.utcnow() + timedelta(days=30)

        try:
            user_uuid = UUID(user_id)
        except (TypeError, ValueError):
            logger.warning(f"Skipping subscription activation for non-UUID user_id: {user_id}")
            return JSONResponse(status_code=200, content={"received": True})

        result = await db.execute(select(Subscription).filter_by(user_id=user_uuid))
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.is_active = True
            subscription.expires_at = expires_at
        else:
            db.add(
                Subscription(
                    user_id=user_uuid,
                    is_active=True,
                    expires_at=expires_at,
                )
            )
        await db.commit()
        logger.info(f"Activated subscription for user {user_uuid}")

    return JSONResponse(status_code=200, content={"received": True})
