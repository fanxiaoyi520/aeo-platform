"""Tests for selection_agent node — MV2-02."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.state import initial_state


def _mock_llm(content: str) -> AsyncMock:
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=content, model="test")
    return provider


_SAMPLE_REPORT = (
    "SKU TEST-001 shows moderate demand with 3 competitors in the niche. "
    "Price positioning is competitive at $29.99. "
    "Recommendation: proceed with listing generation."
)

_BASE_PRODUCT_INFO: dict[str, Any] = {
    "title": "Wireless Charger",
    "price": 29.99,
    "rating": 4.2,
    "review_count": 150,
    "category": "Electronics",
    "brand": "TestBrand",
    "bullet_points": ["Fast charging", "USB-C"],
    "keywords": ["wireless charger", "usb-c charger"],
    "images": ["img1.jpg"],
    "competitors": [
        {"asin": "B001", "price": 25.99, "rating": 4.0, "review_count": 200},
        {"asin": "B002", "price": 34.99, "rating": 4.5, "review_count": 500},
        {"asin": "B003", "price": 28.50, "rating": 3.8, "review_count": 80},
    ],
}


@pytest.mark.asyncio
async def test_selection_node_basic_scoring() -> None:
    from aeo_orchestrator.nodes.selection import selection_node

    state = initial_state(
        task_id="sel-1",
        platform="amazon",
        sku="TEST-001",
        product_info=_BASE_PRODUCT_INFO,
    )
    mock = _mock_llm(_SAMPLE_REPORT)
    with patch("aeo_orchestrator.nodes.selection.get_llm_provider", return_value=mock):
        result = await selection_node(state)

    selection = cast(dict[str, Any], result["selection"])
    assert isinstance(selection, dict)
    assert selection["sku"] == "TEST-001"
    assert 0 <= selection["total_score"] <= 100
    assert selection["competitor_count"] == 3
    assert selection["recommendation"] in ("proceed", "review", "skip")
    assert isinstance(selection["report"], str)
    assert len(selection["report"]) > 0


@pytest.mark.asyncio
async def test_selection_node_no_competitors() -> None:
    from aeo_orchestrator.nodes.selection import selection_node

    info: dict[str, Any] = {"title": "Basic Product", "price": 15.0}
    state = initial_state(
        task_id="sel-2",
        platform="amazon",
        sku="TEST-002",
        product_info=info,
    )
    mock = _mock_llm("No competitors found. Low competition niche.")
    with patch("aeo_orchestrator.nodes.selection.get_llm_provider", return_value=mock):
        result = await selection_node(state)

    selection = cast(dict[str, Any], result["selection"])
    assert selection["competitor_count"] == 0
    assert selection["competition_score"] == 80.0


@pytest.mark.asyncio
async def test_selection_node_trace_events() -> None:
    from aeo_orchestrator.nodes.selection import selection_node

    state = initial_state(
        task_id="sel-3",
        platform="amazon",
        sku="TEST-003",
        product_info=_BASE_PRODUCT_INFO,
    )
    mock = _mock_llm(_SAMPLE_REPORT)
    with patch("aeo_orchestrator.nodes.selection.get_llm_provider", return_value=mock):
        result = await selection_node(state)

    trace = cast(list[dict[str, Any]], result["trace"])
    assert len(trace) == 2
    assert trace[0]["agent"] == "selection_agent"
    assert trace[0]["status"] == "started"
    assert trace[1]["agent"] == "selection_agent"
    assert trace[1]["status"] == "completed"
    assert trace[1]["detail"]["total_score"] > 0


@pytest.mark.asyncio
async def test_selection_node_llm_failure_fallback() -> None:
    from aeo_orchestrator.nodes.selection import selection_node

    state = initial_state(
        task_id="sel-4",
        platform="amazon",
        sku="TEST-004",
        product_info=_BASE_PRODUCT_INFO,
    )
    mock = AsyncMock()
    mock.chat.side_effect = RuntimeError("LLM timeout")
    with patch("aeo_orchestrator.nodes.selection.get_llm_provider", return_value=mock):
        result = await selection_node(state)

    selection = cast(dict[str, Any], result["selection"])
    assert selection["total_score"] > 0
    assert "LLM report generation failed" in selection["report"]
    trace = cast(list[dict[str, Any]], result["trace"])
    statuses = [e["status"] for e in trace]
    assert "failed" in statuses
    assert "completed" in statuses


@pytest.mark.asyncio
async def test_selection_node_completeness_scoring() -> None:
    from aeo_orchestrator.nodes.selection import selection_node

    info: dict[str, Any] = {
        "title": "Full Product",
        "bullet_points": ["a", "b"],
        "keywords": ["kw1"],
        "images": ["img.png"],
        "competitors": [],
    }
    state = initial_state(
        task_id="sel-5",
        platform="amazon",
        sku="TEST-005",
        product_info=info,
    )
    mock = _mock_llm("Full completeness test.")
    with patch("aeo_orchestrator.nodes.selection.get_llm_provider", return_value=mock):
        result = await selection_node(state)

    selection = cast(dict[str, Any], result["selection"])
    assert selection["completeness_score"] == 100.0


def test_extract_competitors_empty() -> None:
    from aeo_orchestrator.nodes.selection import _extract_competitors

    assert _extract_competitors({}) == []
    assert _extract_competitors({"competitors": "not_a_list"}) == []
    assert _extract_competitors({"competitors": [{"asin": ""}]}) == []


def test_extract_competitors_valid() -> None:
    from aeo_orchestrator.nodes.selection import _extract_competitors

    result = _extract_competitors(
        {
            "competitors": [
                {"asin": "B001", "price": "29.99", "rating": 4.0, "review_count": 100},
                {"asin": "B002", "price": None},
            ]
        }
    )
    assert len(result) == 2
    assert result[0].asin == "B001"
    assert result[0].price == 29.99
    assert result[1].price is None


def test_competitor_summary() -> None:
    from aeo_orchestrator.nodes.selection import _competitor_summary
    from aeo_shared.selection_scoring import CompetitorData

    summary = _competitor_summary([])
    assert summary["count"] == 0

    competitors = [
        CompetitorData(asin="A", price=10.0, rating=4.0, review_count=100),
        CompetitorData(asin="B", price=20.0, rating=3.0, review_count=200),
    ]
    summary = _competitor_summary(competitors)
    assert summary["count"] == 2
    assert summary["avg_price"] == 15.0
    assert summary["min_price"] == 10.0
    assert summary["max_price"] == 20.0
