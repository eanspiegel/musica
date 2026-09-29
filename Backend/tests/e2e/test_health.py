import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.settings import get_settings


@pytest.fixture
def client() -> TestClient:
    """Sync test client — /health is excluded from API key middleware."""
    return TestClient(app)


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_expected_body(client: TestClient) -> None:
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


@pytest.mark.asyncio
async def test_health_async() -> None:
    """Async variant using httpx.AsyncClient."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
