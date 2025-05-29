# File: app/api/signals.py

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.core.db import query

router = APIRouter(prefix="/signals", tags=["signals"])


class SignalOut(BaseModel):
    id: int
    asset: str
    signal_type: str
    entry: float
    target: float
    stop_loss: float
    confidence: float
    explanation: str
    created_at: str


@router.get("/", response_model=List[SignalOut])
async def get_signals(
    symbol: Optional[str] = None,
    limit: int = 10,
):
    """
    Возвращает последние сигналы.
    Опционально фильтрует по символу актива.
    """
    sql = """
        SELECT id, asset, signal_type, entry, target, stop_loss, confidence, explanation, created_at
          FROM signals
    """
    params = ()
    if symbol:
        sql += " WHERE asset = ?"
        params = (symbol,)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params = (*params, limit)

    rows = query(sql, params)
    if not rows:
        raise HTTPException(status_code=404, detail="Сигналов не найдено")

    return [
        SignalOut(
            id=r[0],
            asset=r[1],
            signal_type=r[2],
            entry=r[3],
            target=r[4],
            stop_loss=r[5],
            confidence=r[6],
            explanation=r[7],
            created_at=r[8],
        )
        for r in rows
    ]


@router.get("/{signal_id}", response_model=SignalOut)
async def get_signal_detail(signal_id: int):
    """
    Детали конкретного сигнала по его ID.
    """
    rows = query(
        """
        SELECT id, asset, signal_type, entry, target, stop_loss, confidence, explanation, created_at
          FROM signals
         WHERE id = ?
        """,
        (signal_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Сигнал не найден")

    r = rows[0]
    return SignalOut(
        id=r[0],
        asset=r[1],
        signal_type=r[2],
        entry=r[3],
        target=r[4],
        stop_loss=r[5],
        confidence=r[6],
        explanation=r[7],
        created_at=r[8],
    )


@router.get("/history", response_model=List[SignalOut])
async def get_signals_history(limit: int = 100):
    """
    Возвращает историю последних сигналов (до заданного лимита).
    """
    rows = query(
        """
        SELECT id, asset, signal_type, entry, target, stop_loss, confidence, explanation, created_at
          FROM signals
         ORDER BY created_at DESC
         LIMIT ?
        """,
        (limit,),
    )
    return [
        SignalOut(
            id=r[0],
            asset=r[1],
            signal_type=r[2],
            entry=r[3],
            target=r[4],
            stop_loss=r[5],
            confidence=r[6],
            explanation=r[7],
            created_at=r[8],
        )
        for r in rows
    ]
