"""MV4-03 acceptance tests — GET /api/v1/support/scripts."""

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
async def test_list_support_scripts() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/support/scripts", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert len(data["scripts"]) >= 5
    assert data["summary"]["total"] >= 5


@pytest.mark.asyncio
async def test_filter_scripts_by_scenario() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/support/scripts?scenario=return", headers=_HEADERS
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["scripts"]) >= 1
    for script in data["scripts"]:
        assert script["scenario"] == "return"


@pytest.mark.asyncio
async def test_filter_scripts_by_platform() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/support/scripts?platform=amazon", headers=_HEADERS
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["scripts"]) >= 1
    for script in data["scripts"]:
        assert script["platform"] == "amazon"


@pytest.mark.asyncio
async def test_script_has_required_fields() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/support/scripts", headers=_HEADERS)

    data = response.json()["data"]
    script = data["scripts"][0]
    assert "script_id" in script
    assert "scenario" in script
    assert "platform" in script
    assert "template_text" in script
    assert "keywords" in script
    assert len(script["template_text"]) > 0


@pytest.mark.asyncio
async def test_scripts_summary_has_scenarios_list() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/support/scripts", headers=_HEADERS)

    data = response.json()["data"]
    assert "scenarios" in data["summary"]
    assert "return" in data["summary"]["scenarios"]
