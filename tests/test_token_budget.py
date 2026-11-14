import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.services.token_budget import (
    TokenBudget, TokenBudgetExceeded, request_reservation,
)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "usage.sqlite3"

    def test_survives_restart_and_usage_does_not_release_reserve(self):
        budget = TokenBudget(self.path, 100)
        reservation = budget.reserve(70, "model", "2026-11-14")
        budget.record_usage(reservation, 10)
        other = TokenBudget(self.path, 100)
        self.assertEqual(other.status("2026-11-14")["remaining"], 30)
        with self.assertRaises(TokenBudgetExceeded):
            other.reserve(31, "model", "2026-11-14")

    def test_utc_days_have_separate_budgets(self):
        budget = TokenBudget(self.path, 100)
        budget.reserve(100, "model", "2026-11-14")
        budget.reserve(100, "model", "2026-11-15")
        self.assertEqual(budget.status("2026-11-15")["remaining"], 0)

    def test_concurrent_requests_do_not_overbook(self):
        budget = TokenBudget(self.path, 100)
        budget.status()

        def reserve(_):
            try:
                budget.reserve(30, "model")
                return True
            except TokenBudgetExceeded:
                return False

        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve, range(8))), 3)
        self.assertEqual(budget.status()["reserved"], 90)

    def test_zero_limit_blocks_requests(self):
        with self.assertRaises(TokenBudgetExceeded):
            TokenBudget(self.path, 0).reserve(1, "model")

    def test_bounded_text_envelope(self):
        messages = [{"content": "system"}, {"content": "test"}]
        self.assertEqual(request_reservation(messages, 2048), 6154)
        with self.assertRaises(ValueError):
            request_reservation([{"content": "x" * 40000}, {"content": ""}], 2048)
