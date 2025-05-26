# File: app/api/signals.py
from fastapi import APIRouter
from typing import List
from app.core.schemas import Signal

router = APIRouter(prefix="/signals", tags=["signals"])

@router.get("/", response_model=List[Signal])
async def get_signals():
    """Fetch latest trading signals."""
    # TODO: implement signal generation
    return []
