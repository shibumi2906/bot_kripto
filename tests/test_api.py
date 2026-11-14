def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_offline_demo_is_reproducible(client):
    first = client.get("/analysis/demo")
    assert first.status_code == 200
    assert first.json() == client.post("/analysis", json={}).json()
    assert first.json()["core"]["mode"] == "demo"
    assert len(first.json()["core"]["sources"]) == 3
    assert first.json()["ai"]["status"] == "not_requested"


def test_bad_symbol_rejected(client):
    assert client.post("/analysis", json={"symbol": "FAKE"}).status_code == 422


def test_negative_balance_rejected(client):
    assert client.post("/analysis", json={"balance": -10}).status_code == 422


def test_paid_ai_disabled_over_http(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "OPENAI_HTTP_EXPLANATIONS_ENABLED", False)
    assert client.post("/analysis", json={"explain": True}).status_code == 403


def test_quality_failure_is_503(client, monkeypatch):
    from app.domain.analysis import DataQualityError
    import app.api.analysis as api

    async def unavailable(**kwargs):
        raise DataQualityError("At least two fresh independent sources required")

    monkeypatch.setattr(api, "build_report", unavailable)
    assert client.post("/analysis", json={"mode": "live"}).status_code == 503


def test_legacy_payments_not_exposed(client):
    assert client.post("/payments/create-checkout-session", json={}).status_code == 404
