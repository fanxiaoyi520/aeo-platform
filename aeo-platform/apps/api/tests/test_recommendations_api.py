"""Tests for MV3-08: Recommendations API — ads/ops/linkage suggestions + approval."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

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
async def test_get_ads_recommendations() -> None:
    mock_result = {
        "task_id": "rec-ads-1",
        "sku": "TEST-001",
        "platform": "amazon",
        "market": "US",
        "ads": {
            "campaign_summary": [
                {
                    "campaign_id": "camp-001",
                    "name": "Test Campaign",
                    "acos": 15.0,
                    "roi": 3.5,
                }
            ],
            "suggestions": [
                {
                    "campaign_id": "camp-001",
                    "action": "increase_bid",
                    "reason": "Low ACoS, room for scaling",
                }
            ],
            "report": "Campaigns performing well.",
        },
        "trace": [],
    }

    with patch("aeo_orchestrator.runner.run_ads_task", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/recommendations/ads?sku=TEST-001", headers=_HEADERS
            )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert "ads" in data
    assert "suggestions" in data["ads"]


@pytest.mark.asyncio
async def test_get_ops_recommendations() -> None:
    mock_result = {
        "task_id": "rec-ops-1",
        "sku": "TEST-001",
        "platform": "amazon",
        "market": "US",
        "ops": {
            "inventory": [{"sku": "TEST-001", "available_quantity": 50}],
            "health_metrics": {"low_stock_count": 0, "total_available": 50},
            "inventory_alerts": [],
            "pricing_suggestions": [
                {
                    "sku": "TEST-001",
                    "current_price": 29.99,
                    "suggested_price": 32.99,
                    "reason": "Strong inventory, room for margin increase",
                }
            ],
            "restock_recommendations": [],
            "report": "Inventory healthy.",
        },
        "trace": [],
    }

    with patch("aeo_orchestrator.runner.run_ops_task", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/recommendations/ops?sku=TEST-001", headers=_HEADERS
            )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert "ops" in data
    assert "pricing_suggestions" in data["ops"]


@pytest.mark.asyncio
async def test_get_linkage_recommendations() -> None:
    from decimal import Decimal

    from aeo_shared.ads_inventory_linkage import LinkageRecommendation, StockStatus

    mock_recs = [
        LinkageRecommendation(
            campaign_id="camp-001",
            sku="SKU-001",
            stock_status=StockStatus.LOW,
            current_budget=Decimal("20.00"),
            suggested_budget=Decimal("10.00"),
            budget_change_percent=-50.0,
            reason="Low stock, reduce ad spend",
            urgency="high",
        ),
        LinkageRecommendation(
            campaign_id="camp-002",
            sku="SKU-002",
            stock_status=StockStatus.OVERSTOCK,
            current_budget=Decimal("15.00"),
            suggested_budget=Decimal("18.00"),
            budget_change_percent=20.0,
            reason="Overstocked, increase spend",
            urgency="medium",
        ),
    ]

    with patch(
        "aeo_api.routers.recommendations._fetch_linkage_recommendations",
        return_value=mock_recs,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/recommendations/linkage", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert "recommendations" in data
    assert len(data["recommendations"]) == 2
    assert data["recommendations"][0]["campaign_id"] == "camp-001"
    assert data["recommendations"][0]["urgency"] == "high"


@pytest.mark.asyncio
async def test_get_linkage_recommendations_empty() -> None:
    with patch(
        "aeo_api.routers.recommendations._fetch_linkage_recommendations",
        return_value=[],
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/recommendations/linkage", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["recommendations"] == []


@pytest.mark.asyncio
async def test_recommendations_require_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/recommendations/linkage")

    assert response.status_code in (401, 403)
