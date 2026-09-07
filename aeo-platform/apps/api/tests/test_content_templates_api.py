"""Tests for MV2-06 content templates API."""

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
async def test_list_all_content_templates() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/content-templates", headers=_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert len(data["templates"]) == 5
    assert data["summary"]["total"] == 5
    content_types = {t["content_type"] for t in data["templates"]}
    assert "listing" in content_types
    assert "image_copy" in content_types
    assert "tiktok_video" in content_types


@pytest.mark.asyncio
async def test_filter_by_content_type() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/content-templates?content_type=listing", headers=_HEADERS
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["templates"]) == 2
    for tpl in data["templates"]:
        assert tpl["content_type"] == "listing"


@pytest.mark.asyncio
async def test_filter_by_platform() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/content-templates?platform=tiktok", headers=_HEADERS)

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["templates"]) == 3
    for tpl in data["templates"]:
        assert tpl["platform"] == "tiktok"


@pytest.mark.asyncio
async def test_filter_by_both() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/content-templates?content_type=image_copy&platform=amazon",
            headers=_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["templates"]) == 1
    assert data["templates"][0]["content_type"] == "image_copy"
    assert data["templates"][0]["platform"] == "amazon"


@pytest.mark.asyncio
async def test_template_has_required_fields() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/content-templates", headers=_HEADERS)

    data = response.json()["data"]
    tpl = data["templates"][0]
    assert "content_type" in tpl
    assert "platform" in tpl
    assert "system_prompt" in tpl
    assert "output_schema" in tpl
    assert "constraints" in tpl
    assert len(tpl["system_prompt"]) > 0
