from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.domain.analysis import DataQualityError
from app.services.analyst import build_report

router = APIRouter(tags=["analysis"])


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    symbol: Literal["BTCUSDT", "ETHUSDT", "SOLUSDT"] = "BTCUSDT"
    mode: Literal["demo", "live"] = "demo"
    explain: bool = False
    balance: float | None = Field(default=None, gt=0, le=1_000_000_000)
    risk_percent: float = Field(default=0.5, gt=0, le=1)


@router.get("/analysis/demo")
async def demo():
    return await build_report()


@router.post("/analysis")
async def analysis(request: AnalysisRequest):
    if request.explain and not settings.OPENAI_HTTP_EXPLANATIONS_ENABLED:
        raise HTTPException(403, "AI over HTTP is disabled; use CLI --explain locally")
    try:
        return await build_report(**request.model_dump())
    except DataQualityError as exc:
        raise HTTPException(503, str(exc)) from None
