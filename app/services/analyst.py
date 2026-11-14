from copy import deepcopy

from app.domain.analysis import analyze
from app.services.demo_data import DEMO_AS_OF, demo_markets
from app.services.market_sources import fetch_markets
from app.services.signal_generator import explain_report


async def build_report(
    symbol: str = "BTCUSDT", mode: str = "demo", explain: bool = False,
    balance: float | None = None, risk_percent: float = 0.5,
) -> dict:
    if mode == "demo":
        series, failures, now = demo_markets(symbol), {}, DEMO_AS_OF
    elif mode == "live":
        series, failures, now = await fetch_markets(symbol)
    else:
        raise ValueError("Invalid mode")
    core = analyze(series, as_of=now, mode=mode, balance=balance,
                   risk_percent=risk_percent)
    # AI receives a copy; only the separate commentary field is returned.
    ai = await explain_report(deepcopy(core)) if explain else {
        "status": "not_requested", "text": None,
    }
    return {"core": core, "collection_errors": failures, "ai": ai}
