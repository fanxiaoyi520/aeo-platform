"""MV4-06 — GET /api/v1/business-metrics/dashboard API tests."""

from __future__ import annotations

import os

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

from aeo_api.main import app  # noqa: E402

API_KEY = os.environ["AUTH_API_KEY"]
_HEADERS = {"Authorization": f"Bearer {API_KEY}"}


@pytest.mark.asyncio
async def test_get_business_metrics_dashboard() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/business-metrics/dashboard", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert "gmv" in data
    assert "roi" in data
    assert "automation_rate" in data
    assert "trend" in data
    assert "period_days" in data


@pytest.mark.asyncio
async def test_dashboard_has_trend_data() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/business-metrics/dashboard", headers=_HEADERS)

    data = response.json()["data"]
    assert isinstance(data["trend"], list)
    assert len(data["trend"]) > 0
    first_entry = data["trend"][0]
    assert "date" in first_entry
    assert "gmv" in first_entry


@pytest.mark.asyncio
async def test_dashboard_automation_rate_is_valid() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/business-metrics/dashboard", headers=_HEADERS)

    data = response.json()["data"]
    rate = data["automation_rate"]
    if rate is not None:
        from decimal import Decimal

        rate_decimal = Decimal(rate)
        assert Decimal("0") <= rate_decimal <= Decimal("1")
