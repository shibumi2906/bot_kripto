# File: tests/test_api.py
import pytest

def test_signals_endpoint(client):
    """Test GET /signals returns empty list."""
    response = client.get("/signals/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.parametrize("path, expected_keys", [
    ("/analytics/onchain", ["active_addresses", "tx_count"]),
    ("/portfolio/", ["assets", "total_value"]),
])
def test_api_endpoints_keys(client, path, expected_keys):
    """Test API endpoints return correct JSON structure."""
    response = client.get(path)
    assert response.status_code == 200
    data = response.json()
    for key in expected_keys:
        assert key in data
