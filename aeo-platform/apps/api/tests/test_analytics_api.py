"""MV4-04 acceptance tests — GET /api/v1/analytics/report."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

from aeo_api.db.models import get_db_session
from aeo_api.main import app  # noqa: E402

API_KEY = os.environ["AUTH_API_KEY"]
_HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def _mock_db_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_get_analytics_report() -> None:
    app.dependency_overrides[get_db_session] = lambda: _mock_db_session()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/analytics/report", headers=_HEADERS)

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        data = body["data"]
        assert "report" in data
        assert "generated_at" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analytics_report_has_metrics_summary() -> None:
    app.dependency_overrides[get_db_session] = lambda: _mock_db_session()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/analytics/report", headers=_HEADERS)

        data = response.json()["data"]
        assert "metrics_summary" in data
        metrics = data["metrics_summary"]
        assert "total_gmv" in metrics
        assert "total_ad_spend" in metrics
        assert "total_orders" in metrics
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analytics_report_returns_data_source() -> None:
    app.dependency_overrides[get_db_session] = lambda: _mock_db_session()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/analytics/report", headers=_HEADERS)

        data = response.json()["data"]
        assert "data_source" in data
        assert data["data_source"] in ("live", "mock")
    finally:
        app.dependency_overrides.clear()
