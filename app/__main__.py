"""python -m app analyze --mode demo|live [--explain]"""
import argparse
import asyncio
import json
import sys

from app.domain.analysis import DataQualityError
from app.services.analyst import build_report
from app.services.token_budget import TokenBudget
from app.core.config import settings


def main():
    parser = argparse.ArgumentParser(description="Deterministic crypto market analyst")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--mode", choices=["demo", "live"], default="demo")
    analyze.add_argument("--symbol", choices=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                         default="BTCUSDT")
    analyze.add_argument("--explain", action="store_true", help="Calls OpenAI; may be billable")
    analyze.add_argument("--balance", type=float)
    analyze.add_argument("--risk-percent", type=float, default=0.5)
    sub.add_parser("budget")
    sub.add_parser("doctor", help="Read-only model and Telegram credential checks")
    args = parser.parse_args()
    if args.command == "doctor":
        from app.services.diagnostics import check_credentials
        print(json.dumps(check_credentials(), indent=2))
        return
    if args.command == "budget":
        print(json.dumps(TokenBudget(
            settings.OPENAI_BUDGET_DB, settings.OPENAI_DAILY_TOKEN_LIMIT,
        ).status(), indent=2))
        return
    try:
        result = asyncio.run(build_report(
            symbol=args.symbol, mode=args.mode, explain=args.explain,
            balance=args.balance, risk_percent=args.risk_percent,
        ))
    except (DataQualityError, ValueError) as exc:
        print(f"Analysis unavailable: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
