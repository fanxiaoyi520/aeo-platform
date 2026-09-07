"""MV4-05 — POST /api/v1/analytics/create_tasks API tests."""

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
async def test_create_tasks_from_suggestions() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analytics/create_tasks",
            headers=_HEADERS,
            json={
                "parent_task_id": "analytics-api-test",
                "suggestions": [
                    {"action": "increase_ad_spend", "sku": "SKU-001", "reason": "High ROI"},
                    {"action": "restock", "sku": "SKU-002", "reason": "Low stock"},
                ],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert "created_tasks" in data
    tasks = data["created_tasks"]
    assert len(tasks) == 2
    assert tasks[0]["agent_id"] == "ads_agent"
    assert tasks[1]["agent_id"] == "operations_agent"


@pytest.mark.asyncio
async def test_create_tasks_filters_unknown_actions() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analytics/create_tasks",
            headers=_HEADERS,
            json={
                "suggestions": [
                    {"action": "unknown_action", "sku": "SKU-001", "reason": "test"},
                    {"action": "increase_ad_spend", "sku": "SKU-002", "reason": "good ROI"},
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    tasks = data["created_tasks"]
    assert len(tasks) == 1
    assert tasks[0]["agent_id"] == "ads_agent"


@pytest.mark.asyncio
async def test_create_tasks_empty_suggestions() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analytics/create_tasks",
            headers=_HEADERS,
            json={"suggestions": []},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["created_tasks"] == []
