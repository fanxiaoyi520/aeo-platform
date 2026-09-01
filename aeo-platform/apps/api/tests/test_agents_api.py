"""Tests for MV4-07 agents command console API."""

from __future__ import annotations

from aeo_api.main import app
from httpx import ASGITransport, AsyncClient

_HEADERS = {"Authorization": "Bearer dev-api-key-change-in-production"}


async def test_list_agents_returns_catalog() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["summary"]["total"] >= 10
    assert data["summary"]["active"] >= 6
    assert data["summary"]["planned"] >= 5
    agent_ids = {item["agent_id"] for item in data["agents"]}
    assert "research_agent" in agent_ids
    assert "selection_agent" in agent_ids


async def test_list_agents_includes_listing_graph() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents", headers=_HEADERS)

    graphs = response.json()["data"]["graphs"]
    listing = next(item for item in graphs if item["graph_id"] == "listing")
    assert listing["step_count"] == 6
    assert listing["agent_ids"][0] == "research_agent"
