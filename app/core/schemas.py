# File: app/core/schemas.py

from pydantic import BaseModel
from pydantic import ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# ----------------------------
# User schemas
# ----------------------------

class UserCreate(BaseModel):
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str


# ----------------------------
# Subscription schemas
# ----------------------------

class SubscriptionStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_active: bool
    expires_at: Optional[datetime]


# ----------------------------
# Signal schema
# ----------------------------

class Signal(BaseModel):
    action: str
    entry: float
    target: float
    stop_loss: float
    confidence: float


# ----------------------------
# Portfolio schemas
# ----------------------------

class PortfolioAsset(BaseModel):
    symbol: str
    amount: float
    value_usd: float


class PortfolioOut(BaseModel):
    assets: List[PortfolioAsset]
    total_value: float


# ----------------------------
# On-chain metrics schema
# ----------------------------

class OnChainMetricsOut(BaseModel):
    active_addresses: int
    tx_count: int

