# File: app/services/payment_service.py
import uuid
import hmac
import hashlib
import httpx
from typing import Dict, Any
from fastapi import HTTPException, Request
from app.core.config import settings
from app.core.logger import logger

YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"

async def create_yookassa_payment(user_id: str, plan: str) -> str:
    """
    Create a payment in YooKassa and return the confirmation URL.
    plan must map to a price value in settings.YOOKASSA_PRICES dict.
    """
    amount = settings.YOOKASSA_PRICES.get(plan)
    if amount is None:
        raise HTTPException(status_code=400, detail="Unknown plan for Yookassa payment")

    idempotence_key = str(uuid.uuid4())
    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": settings.YOOKASSA_CURRENCY
        },
        "confirmation": {
            "type": "redirect",
            "return_url": settings.DOMAIN + settings.YOOKASSA_RETURN_PATH
        },
        "capture": True,
        "metadata": {"user_id": user_id, "plan": plan}
    }
    headers = {
        "Idempotence-Key": idempotence_key,
        "Content-Type": "application/json"
    }
    auth = (settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY)
    async with httpx.AsyncClient() as client:
        resp = await client.post(YOOKASSA_API_URL, auth=auth, json=payload, headers=headers)
    if resp.status_code not in (200, 201):
        logger.error(f"YooKassa create payment failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=502, detail="YooKassa payment creation failed")

    data = resp.json()
    confirmation = data.get("confirmation", {})
    url = confirmation.get("confirmation_url")
    if not url:
        logger.error(f"No confirmation URL in YooKassa response: {data}")
        raise HTTPException(status_code=502, detail="Invalid YooKassa response")
    logger.info(f"YooKassa payment created for user {user_id}, plan {plan}, url: {url}")
    return url

async def handle_yookassa_webhook(request: Request) -> Dict[str, Any]:
    """
    Process incoming YooKassa webhook. Verify signature and return parsed event.
    """
    signature = request.headers.get("X-Request-Signature")
    body = await request.body()
    # Verify signature: HMAC-SHA256 of body with secret key
    expected_sig = hmac.new(
        settings.YOOKASSA_SECRET_KEY.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature or "", expected_sig):
        logger.error("Invalid YooKassa webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event = await request.json()
    obj = event.get("object", {})
    event_type = event.get("event")
    metadata = obj.get("metadata", {})
    logger.info(f"YooKassa webhook received: {event_type} for user {metadata.get('user_id')}")
    # Return parsed data for API handler to update DB
    return {"event": event_type, "object": obj, "metadata": metadata}
