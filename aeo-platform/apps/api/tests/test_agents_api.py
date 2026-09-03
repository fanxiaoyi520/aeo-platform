"""Tests for MV4-07 agents command console API."""

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
async def test_list_agents_returns_catalog() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["summary"]["total"] >= 10
    assert data["summary"]["active"] >= 7
    assert data["summary"]["planned"] >= 4
    agent_ids = {item["agent_id"] for item in data["agents"]}
    assert "research_agent" in agent_ids
    assert "selection_agent" in agent_ids


@pytest.mark.asyncio
async def test_list_agents_includes_listing_graph() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents", headers=_HEADERS)

    graphs = response.json()["data"]["graphs"]
    listing = next(item for item in graphs if item["graph_id"] == "listing")
    assert listing["step_count"] == 6
    assert listing["agent_ids"][0] == "research_agent"
