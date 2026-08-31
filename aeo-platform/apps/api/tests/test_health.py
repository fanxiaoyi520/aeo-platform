import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Set env before importing app
os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

from aeo_api.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"
    assert "request_id" in body
    assert response.headers.get("X-Request-ID")


@pytest.mark.asyncio
async def test_ready_all_ok(client: AsyncClient) -> None:
    with (
        patch("aeo_api.routers.health.check_database", new_callable=AsyncMock, return_value=True),
        patch("aeo_api.routers.health.check_redis", new_callable=AsyncMock, return_value=True),
    ):
        response = await client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ready"
    assert body["data"]["database"] is True
    assert body["data"]["redis"] is True


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_unauthorized_without_api_key(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tasks", headers={})
    assert response.status_code == 401
