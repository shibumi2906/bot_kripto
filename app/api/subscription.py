# app/api/subscription.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

import sqlite3

from app.core.db import query
from app.api.auth import get_current_user

router = APIRouter(prefix="/subscription", tags=["subscription"])


class SubscriptionOut(BaseModel):
    is_active: bool
    provider: str | None
    expires_at: datetime | None


@router.get("/status", response_model=SubscriptionOut)
async def subscription_status(current: dict = Depends(get_current_user)):
    """
    Возвращает статус подписки текущего пользователя.
    """
    user_id = current["id"]
    rows = query(
        "SELECT status, provider, expires_at FROM subscriptions WHERE telegram_id = ?",
        (user_id,),
    )
    if not rows:
        return SubscriptionOut(is_active=False, provider=None, expires_at=None)

    status_str, provider, expires = rows[0]
    expires_dt = datetime.fromisoformat(expires) if expires else None
    is_active = status_str.lower() == "active" and (expires_dt is None or expires_dt > datetime.utcnow())
    return SubscriptionOut(is_active=is_active, provider=provider, expires_at=expires_dt)
