import asyncio
from types import SimpleNamespace

from app.core.config import settings
from app.services.demo_data import demo_markets, DEMO_AS_OF
from app.domain.analysis import analyze
from app.services import signal_generator
from app.services.token_budget import TokenBudget


def test_ai_usage_accounting_and_request_parameters(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "unit-test-not-a-real-key")
    monkeypatch.setattr(settings, "OPENAI_BUDGET_DB", str(tmp_path / "budget.sqlite3"))

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.chat = SimpleNamespace(completions=self)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def create(self, **kwargs):
            captured["request"] = kwargs
            return SimpleNamespace(
                usage=SimpleNamespace(total_tokens=100),
                choices=[SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(content="Commentary, not a decision."),
                )],
            )

    monkeypatch.setattr(signal_generator, "AsyncOpenAI", FakeClient)
    core = analyze(demo_markets("BTCUSDT"), as_of=DEMO_AS_OF, mode="demo")
    result = asyncio.run(signal_generator.explain_report(core))
    assert result["status"] == "ok"
    assert captured["request"]["model"] == settings.OPENAI_MODEL
    assert captured["request"]["reasoning_effort"] == "low"
    assert "temperature" not in captured["request"]
    assert captured["client"]["max_retries"] == 0
    status = TokenBudget(settings.OPENAI_BUDGET_DB, 200000).status()
    assert status["reported_usage"] == 100
    assert 100 < status["reserved"] < 200000


def test_budget_blocks_before_api_client_creation(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "unit-test-not-a-real-key")
    monkeypatch.setattr(settings, "OPENAI_DAILY_TOKEN_LIMIT", 0)
    monkeypatch.setattr(settings, "OPENAI_BUDGET_DB", str(tmp_path / "budget.sqlite3"))

    def fail(**kwargs):
        raise AssertionError("API client must not be created")

    monkeypatch.setattr(signal_generator, "AsyncOpenAI", fail)
    assert asyncio.run(signal_generator.explain_report({}))["status"] == "budget_exhausted"
