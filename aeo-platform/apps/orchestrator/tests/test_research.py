from unittest.mock import AsyncMock, patch

import pytest
from aeo_orchestrator.nodes.research import research_node
from aeo_orchestrator.state import initial_state


@pytest.mark.asyncio
async def test_research_uses_user_competitors() -> None:
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
