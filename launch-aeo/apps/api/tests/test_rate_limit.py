import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

API_KEY = os.environ["AUTH_API_KEY"]

from aeo_api.config import Settings, validate_production_settings  # noqa: E402
from aeo_api.main import app  # noqa: E402


class FakeRedis:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    async def expire(self, key: str, seconds: int) -> bool:
        return True


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.mark.asyncio
async def test_rate_limit_returns_429_after_limit(
    client: AsyncClient, fake_redis: FakeRedis
) -> None:
    with (
        patch("aeo_api.middleware.rate_limit.get_redis", new_callable=AsyncMock) as mock_get,
        patch("aeo_api.routers.tasks._service.list_tasks", new_callable=AsyncMock) as mock_list,
    ):
        mock_get.return_value = fake_redis
        mock_list.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
        }

        for _ in range(100):
            response = await client.get("/api/v1/tasks")
            assert response.status_code == 200

        response = await client.get("/api/v1/tasks")
        assert response.status_code == 429
        body = response.json()
        assert body["code"] == 10003
        assert response.headers.get("Retry-After") == "60"


@pytest.mark.asyncio
async def test_cors_allows_configured_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/tasks",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


@pytest.mark.asyncio
async def test_public_paths_skip_rate_limit(client: AsyncClient, fake_redis: FakeRedis) -> None:
    with patch("aeo_api.middleware.rate_limit.get_redis", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_redis
        for _ in range(150):
            response = await client.get("/health")
            assert response.status_code == 200


def test_production_rejects_default_api_key() -> None:
    settings = Settings(
        APP_ENV="production",
        APP_NAME="launch-aeo",
        DB_URL="postgresql+asyncpg://aeo:aeo@localhost:5432/aeo",
        DB_URL_SYNC="postgresql+psycopg://aeo:aeo@localhost:5432/aeo",
        AUTH_API_KEY="dev-api-key-change-in-production",
    )
    with pytest.raises(RuntimeError, match="AUTH_API_KEY"):
        validate_production_settings(settings)


def test_production_accepts_custom_api_key() -> None:
    settings = Settings(
        APP_ENV="production",
        APP_NAME="launch-aeo",
        DB_URL="postgresql+asyncpg://aeo:aeo@localhost:5432/aeo",
        DB_URL_SYNC="postgresql+psycopg://aeo:aeo@localhost:5432/aeo",
        AUTH_API_KEY="secure-production-key",
    )
    validate_production_settings(settings)
