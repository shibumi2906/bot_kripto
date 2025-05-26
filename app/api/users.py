# File: app/api/users.py
from fastapi import APIRouter, HTTPException, status
from typing import Optional
from app.core.schemas import UserCreate, UserOut, SubscriptionStatus

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate):
    """Register a new user and create a default subscription status."""
    # TODO: implement user creation logic
    return UserOut(id="", username=user.username)

@router.get("/{user_id}/subscription", response_model=SubscriptionStatus)
async def get_subscription_status(user_id: str):
    """Return subscription status for a given user."""
    # TODO: fetch from DB
    return SubscriptionStatus(status="inactive", expires_at=None)
