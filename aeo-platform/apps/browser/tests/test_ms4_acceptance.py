"""MS4 browser automation acceptance tests — S4-04."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aeo_browser import fetch_listing, is_browser_enabled, search_competitors
from aeo_orchestrator.nodes.research import research_node
from aeo_orchestrator.state import initial_state


def test_ms4_browser_package_exports() -> None:
    assert callable(fetch_listing)
    assert callable(search_competitors)
    assert callable(is_browser_enabled)


def test_ms4_fetch_listing_schema_documented() -> None:
    module_doc = Path(__file__).resolve().parents[1] / "src" / "aeo_browser" / "fetcher.py"
    text = module_doc.read_text(encoding="utf-8")
    assert "screenshot_path" in text
    assert "fetched_at" in text


@pytest.mark.asyncio
async def test_ms4_research_degrades_when_browser_fetch_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BROWSER_ENABLED", "true")
    state = initial_state(
        task_id="ms4-degrade",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B07JFSRMBH"]},
    )
    with patch(
        "aeo_browser.fetch_listing",
        new_callable=AsyncMock,
        side_effect=RuntimeError("captcha detected"),
    ):
        result = await research_node(state)
    research = result["research"]
    assert isinstance(research, dict)
    assert result["degraded_mode"] is True
    assert research["competitors"][0]["source"] == "user_input"


@pytest.mark.asyncio
async def test_ms4_research_enriches_on_browser_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BROWSER_ENABLED", "true")
    state = initial_state(
        task_id="ms4-ok",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B07JFSRMBH"]},
    )
    listing = {
        "asin": "B07JFSRMBH",
        "title": "Acme Competitor",
        "bullets": ["Feature A"],
        "price": "$199.00",
        "rating": 4.6,
        "review_count": 500,
        "screenshot_path": "data/screenshots/test.png",
        "fetched_at": "2026-08-30T00:00:00+00:00",
    }
    with patch("aeo_browser.fetch_listing", new_callable=AsyncMock, return_value=listing):
        result = await research_node(state)
    research = result["research"]
    assert isinstance(research, dict)
    competitor = research["competitors"][0]
    assert competitor["title"] == "Acme Competitor"
    assert result["degraded_mode"] is False
