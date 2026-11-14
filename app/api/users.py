from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.models import Subscription, User
from app.core.schemas import SubscriptionStatus, UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).filter_by(username=user.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    new_user = User(username=user.username)
    new_user.subscription = Subscription(is_active=False, expires_at=None)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get(
    "/{user_id}/subscription",
    response_model=SubscriptionStatus,
)
async def get_subscription_status(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subscription).filter_by(user_id=user_id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    return subscription
