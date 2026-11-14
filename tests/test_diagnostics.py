from types import SimpleNamespace

from app.core.config import settings
from app.services import diagnostics


def test_diagnostics_never_returns_exception_text_or_keys(monkeypatch):
    secret = "fake-private-value"
    monkeypatch.setattr(settings, "OPENAI_API_KEY", secret)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", secret)

    def fail(*args, **kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(diagnostics, "OpenAI", fail)
    monkeypatch.setattr(diagnostics.httpx, "get", fail)
    result = diagnostics.check_credentials()
    assert secret not in str(result)
    assert result["openai"]["error_type"] == "RuntimeError"
    assert result["telegram"]["status"] == "failed"


def test_missing_keys_skip_network(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", None)
    assert diagnostics.check_credentials() == {
        "openai": {"status": "not_configured"},
        "telegram": {"status": "not_configured"},
    }
