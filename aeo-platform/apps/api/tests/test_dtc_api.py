"""Tests for P3-08 DTC dashboard API."""

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
async def test_dtc_dashboard_returns_200() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dtc/dashboard", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_dtc_dashboard_has_storefront() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dtc/dashboard", headers=_HEADERS)

    data = response.json()["data"]
    storefront = data["storefront"]
    assert "total_products" in storefront
    assert "active_products" in storefront
    assert "total_orders" in storefront
    assert "paid_orders" in storefront
    assert "low_stock_items" in storefront
    assert "active_discounts" in storefront
    assert storefront["total_products"] > 0


@pytest.mark.asyncio
async def test_dtc_dashboard_has_kpis() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dtc/dashboard", headers=_HEADERS)

    kpis = response.json()["data"]["kpis"]
    assert "avg_conversion_rate" in kpis
    assert "avg_cart_abandonment_rate" in kpis
    assert "avg_order_value" in kpis
    assert "total_revenue" in kpis
    assert "customer_lifetime_value" in kpis
    assert "repeat_purchase_rate" in kpis
    assert "metric_days" in kpis
    assert kpis["metric_days"] > 0


@pytest.mark.asyncio
async def test_dtc_dashboard_has_abandoned_carts_summary() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dtc/dashboard", headers=_HEADERS)

    summary = response.json()["data"]["abandoned_carts_summary"]
    assert "total" in summary
    assert "recovery_email_sent" in summary
    assert "total_value" in summary
    assert summary["total"] > 0


@pytest.mark.asyncio
async def test_dtc_dashboard_has_recent_orders() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dtc/dashboard", headers=_HEADERS)

    orders = response.json()["data"]["recent_orders"]
    assert isinstance(orders, list)
    assert len(orders) > 0
    assert len(orders) <= 5


@pytest.mark.asyncio
async def test_dtc_dashboard_has_top_products() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dtc/dashboard", headers=_HEADERS)

    products = response.json()["data"]["top_products"]
    assert isinstance(products, list)
    assert len(products) > 0
    assert len(products) <= 5
