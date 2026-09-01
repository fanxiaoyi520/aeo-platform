from unittest.mock import AsyncMock, patch

import pytest
from aeo_orchestrator.nodes.research import research_node
from aeo_orchestrator.state import initial_state


@pytest.mark.asyncio
async def test_research_uses_user_competitors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BROWSER_ENABLED", "false")
    state = initial_state(
        task_id="t1",
        platform="amazon",
        sku="DEMO-001",
        product_info={
            "competitor_asins": ["B001", "B002"],
            "keywords": ["OBD2", "scanner"],
        },
    )
    result = await research_node(state)
    research = result["research"]
    assert isinstance(research, dict)
    assert len(research["competitors"]) == 2
    assert research["degraded"] is False
    assert result["degraded_mode"] is False


@pytest.mark.asyncio
async def test_research_enriches_with_browser_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BROWSER_ENABLED", "true")
    state = initial_state(
        task_id="t3",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B07JFSRMBH"]},
    )
    listing = {
        "asin": "B07JFSRMBH",
        "title": "Competitor Title",
        "price": "$99.00",
        "source": "browser",
    }
    with patch(
        "aeo_browser.fetch_listing",
        new_callable=AsyncMock,
        return_value=listing,
    ):
        result = await research_node(state)
    research = result["research"]
    assert isinstance(research, dict)
    competitors = research["competitors"]
    assert competitors[0]["title"] == "Competitor Title"
    assert competitors[0]["source"] == "browser"


@pytest.mark.asyncio
async def test_research_degraded_when_all_browser_fetches_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BROWSER_ENABLED", "true")
    state = initial_state(
        task_id="t4",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B001", "B002"]},
    )
    with patch(
        "aeo_browser.fetch_listing",
        new_callable=AsyncMock,
        side_effect=RuntimeError("network down"),
    ):
        result = await research_node(state)
    research = result["research"]
    assert isinstance(research, dict)
    assert len(research["competitors"]) == 2
    assert research["degraded"] is True
    assert result["degraded_mode"] is True
    assert all(c.get("source") == "user_input" for c in research["competitors"])


@pytest.mark.asyncio
async def test_research_degraded_without_competitors() -> None:
    state = initial_state(task_id="t2", platform="amazon", sku="DEMO-001")
    with patch(
        "aeo_orchestrator.nodes.research._expand_keywords_with_llm",
        new_callable=AsyncMock,
        return_value=["obd2", "diagnostic"],
    ):
        result = await research_node(state)
    research = result["research"]
    assert isinstance(research, dict)
    assert research["degraded"] is True
    assert result["degraded_mode"] is True
    assert research["keywords"] == ["obd2", "diagnostic"]


@pytest.mark.asyncio
async def test_research_enriches_product_info_from_mock_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BROWSER_ENABLED", "false")
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "mock")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()
    state = initial_state(
        task_id="t5",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={"competitor_asins": ["B001"]},
    )
    result = await research_node(state)
    product_info = result["product_info"]
    assert isinstance(product_info, dict)
    research = result["research"]
    assert isinstance(research, dict)
    assert product_info["title"] == "HomeBrew Electric Kettle 1L"
    assert product_info["brand"] == "HomeBrew"
    assert research["amazon_listing_loaded"] is True
    assert research["degraded"] is False
