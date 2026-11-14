# File: app/core/schemas.py
from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str


class SubscriptionStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_active: bool = False
    expires_at: datetime | None = None


class Signal(BaseModel):
    action: str
    entry: float
    target: float
    stop_loss: float
    confidence: float


class PortfolioAsset(BaseModel):
    symbol: str
    amount: float
    value_usd: float = 0.0


class PortfolioOut(BaseModel):
    assets: List[PortfolioAsset]
    total_value: float


class OnChainMetricsOut(BaseModel):
    active_addresses: int
    tx_count: int


class CheckoutSessionRequest(BaseModel):
    user_id: str
    plan: str
