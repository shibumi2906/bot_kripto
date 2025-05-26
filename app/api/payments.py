# File: app/api/payments.py
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import stripe
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.core.db import get_db
from app.core.models import Subscription

router = APIRouter(prefix="/payments", tags=["payments"])

# Configure Stripe
stripe.api_key = settings.STRIPE_API_KEY
STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET  # add to config

@router.post("/create-checkout-session")
async def create_checkout_session(user_id: str, plan: str):
    """Create a Stripe Checkout session for the given user and plan."""
    # TODO: map plan to Stripe Price ID
    price_id = settings.STRIPE_PRICE_IDS.get(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Unknown plan")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"user_id": user_id, "plan": plan},
            success_url=settings.DOMAIN + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.DOMAIN + "/cancel"
        )
        return {"sessionId": session.id}
    except Exception as e:
        logger.error(f"Stripe session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Process checkout.session.completed
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        user_id = session_obj['metadata'].get('user_id')
        # Activate or update subscription
        expires_at = datetime.utcnow() + timedelta(days=30)  # adjust per plan
        result = await db.execute(select(Subscription).filter_by(user_id=user_id))
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.is_active = True
            subscription.expires_at = expires_at
        else:
            subscription = Subscription(
                user_id=user_id,
                is_active=True,
                expires_at=expires_at
            )
            db.add(subscription)
        await db.commit()
        logger.info(f"Activated subscription for user {user_id}")

    return JSONResponse(status_code=200, content={"received": True})
