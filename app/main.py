from fastapi import FastAPI

from app.api.analysis import router

app = FastAPI(
    title="Crypto Analyst: Deterministic Core + AI",
    version="0.3.0",
    description=(
        "Reproducible technical analysis from closed hourly candles. "
        "Demo runs offline. Live uses Binance, OKX and Kraken. "
        "AI commentary is optional and cannot modify the core report."
    ),
)
app.include_router(router)


@app.get("/health")
async def healthcheck():
    return {"status": "ok", "engine": "technical-v2"}
