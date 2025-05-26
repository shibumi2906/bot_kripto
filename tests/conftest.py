# File: tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    """Test client for FastAPI application."""
    return TestClient(app)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for all tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
