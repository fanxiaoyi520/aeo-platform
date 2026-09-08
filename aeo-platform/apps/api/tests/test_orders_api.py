"""Tests for MV4-01 orders API."""

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
async def test_list_orders_returns_mock_data() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/orders", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert "orders" in data
    assert "total" in data
    assert data["total"] >= 1
    first = data["orders"][0]
    assert "order_id" in first
    assert "sku" in first
    assert "platform" in first


@pytest.mark.asyncio
async def test_list_orders_filter_by_sku() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/orders?sku=PILOT-001", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    for order in body["data"]["orders"]:
        assert order["sku"] == "PILOT-001"


@pytest.mark.asyncio
async def test_list_orders_filter_by_platform() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/orders?platform=amazon", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    for order in body["data"]["orders"]:
        assert order["platform"] == "amazon"


@pytest.mark.asyncio
async def test_list_orders_pagination() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/orders?page=1&page_size=2", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert len(body["data"]["orders"]) <= 2


@pytest.mark.asyncio
async def test_orders_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/orders")

    assert response.status_code == 401
