# File: app/core/schemas.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# User schemas
type Engine = Optional[str]
class UserCreate(BaseModel):
    username: str

class UserOut(BaseModel):
    id: UUID
    username: str
    class Config:
        orm_mode = True

# Subscription schemas
class SubscriptionStatus(BaseModel):
    is_active: bool
    expires_at: Optional[datetime]
    class Config:
        orm_mode = True

# Signal schema
class Signal(BaseModel):
    action: str
    entry: float
    target: float
    stop_loss: float
    confidence: float

# Portfolio schemas
class PortfolioAsset(BaseModel):
    symbol: str
    amount: float
    value_usd: float

class PortfolioOut(BaseModel):
    assets: List[PortfolioAsset]
    total_value: float

# On-chain metrics schema
class OnChainMetricsOut(BaseModel):
    active_addresses: int
    tx_count: int

class Config:
    orm_mode = True
