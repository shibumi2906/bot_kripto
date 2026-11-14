"""Persistent, conservative reservations for this application's OpenAI requests."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class TokenBudgetExceeded(RuntimeError):
    pass


def request_reservation(messages: list[dict[str, str]], max_output: int) -> int:
    if not 256 <= max_output <= 8192:
        raise ValueError("Invalid output limit")
    # For bounded text-only requests, UTF-8 bytes overestimate text tokens.
    # Extra headroom covers the fixed chat framing. No tools, media or history.
    size = sum(len(m["content"].encode("utf-8")) for m in messages)
    if len(messages) != 2 or size > 32_768:
        raise ValueError("Request exceeds the supported text budget envelope")
    return size + 4096 + max_output


class TokenBudget:
    def __init__(self, path: str | Path, daily_limit: int):
        if not 0 <= daily_limit <= 200_000:
            raise ValueError("Daily limit must be between 0 and 200000")
        self.path = Path(path)
        self.limit = daily_limit

    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        db.execute(
            "CREATE TABLE IF NOT EXISTS reservations ("
            "id INTEGER PRIMARY KEY, day TEXT NOT NULL, model TEXT NOT NULL, "
            "reserved INTEGER NOT NULL, actual INTEGER)"
        )
        db.commit()
        return db

    def reserve(self, tokens: int, model: str, day: str | None = None) -> int:
        if tokens <= 0:
            raise ValueError("Reservation must be positive")
        day = day or datetime.now(timezone.utc).date().isoformat()
        db = self._connect()
        try:
            # Serializes admission across API workers and bot processes.
            db.execute("BEGIN IMMEDIATE")
            used = db.execute(
                "SELECT COALESCE(SUM(reserved), 0) FROM reservations WHERE day = ?",
                (day,),
            ).fetchone()[0]
            if used + tokens > self.limit:
                raise TokenBudgetExceeded("OpenAI daily token budget exhausted (UTC)")
            cursor = db.execute(
                "INSERT INTO reservations(day, model, reserved) VALUES (?, ?, ?)",
                (day, model, tokens),
            )
            db.commit()
            return cursor.lastrowid
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def record_usage(self, reservation_id: int, actual: int) -> None:
        if actual < 0:
            raise ValueError("Usage cannot be negative")
        db = self._connect()
        try:
            db.execute(
                "UPDATE reservations SET actual = ? WHERE id = ?",
                (actual, reservation_id),
            )
            db.commit()
        finally:
            db.close()

    def status(self, day: str | None = None) -> dict:
        day = day or datetime.now(timezone.utc).date().isoformat()
        db = self._connect()
        try:
            reserved, actual = db.execute(
                "SELECT COALESCE(SUM(reserved), 0), COALESCE(SUM(actual), 0) "
                "FROM reservations WHERE day = ?", (day,),
            ).fetchone()
            return {
                "day_utc": day, "limit": self.limit, "reserved": reserved,
                "reported_usage": actual, "remaining": max(0, self.limit - reserved),
            }
        finally:
            db.close()
