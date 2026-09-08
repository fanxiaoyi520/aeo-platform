"""MV4-04 acceptance tests — A06 Analytics Agent end-to-end."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_analytics_agent_active_in_registry() -> None:
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    agent = registry.get("analytics_agent")
    assert agent.status == "active"
    assert agent.graph_node == "analytics"
    assert agent.category.value == "A06"
    capability_names = [c.name for c in agent.capabilities]
    assert "analytics.daily_report" in capability_names
    assert "analytics.weekly_report" in capability_names


def test_analytics_subgraph_registered() -> None:
    from aeo_shared import get_subgraph

    graph = get_subgraph("analytics")
    assert graph.graph_id == "analytics"
    assert "analytics_agent" in graph.agent_ids


def test_analytics_graph_builds() -> None:
    from aeo_orchestrator.graph import build_analytics_graph

    graph = build_analytics_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_analytics_graph_e2e() -> None:
    from aeo_orchestrator.graph import build_analytics_graph
    from aeo_orchestrator.state import initial_state

    graph = build_analytics_graph()
    state = initial_state(
        task_id="mv4-04-e2e",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={
            "title": "HomeBrew Electric Kettle 1L",
            "price": 29.99,
            "category": "Home & Kitchen",
        },
    )

    mock_llm_response = json.dumps(
        {
            "daily_summary": "GMV $1,234 with 42 orders. ROI improved to 3.2x.",
            "weekly_trend": "Revenue up 12% week-over-week. Ad spend stable.",
            "strategy_suggestions": [
                {
                    "action": "increase_ad_spend",
                    "sku": "HOMEBREW-KETTLE-1L",
                    "reason": "Strong ROI supports higher ad budget",
                }
            ],
            "kpi_targets": {
                "daily_gmv_target": 1000,
                "daily_gmv_actual": 1234,
                "target_met": True,
            },
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "mv4-04-e2e"}})

    analytics = result.get("analytics")
    assert analytics is not None
    assert "daily_summary" in analytics
    assert "weekly_trend" in analytics
    assert "strategy_suggestions" in analytics
    assert "kpi_targets" in analytics
    assert "report" in analytics

    assert isinstance(analytics["daily_summary"], str)
    assert len(analytics["daily_summary"]) > 0

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "analytics_agent"]
    assert len(agent_events) >= 2
    assert agent_events[0]["status"] == "started"
    assert agent_events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_run_analytics_task() -> None:
    from aeo_orchestrator.runner import run_analytics_task

    mock_llm_response = json.dumps(
        {
            "daily_summary": "GMV $500 with 20 orders.",
            "weekly_trend": "Stable performance.",
            "strategy_suggestions": [],
            "kpi_targets": {"target_met": False},
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
        result = await run_analytics_task(
            sku="HOMEBREW-KETTLE-1L",
            product_info={"title": "Electric Kettle", "price": 29.99},
            task_id="runner-analytics-1",
        )

    assert result["task_id"] == "runner-analytics-1"
    assert result["analytics"] is not None


def test_serialize_analytics_result() -> None:
    from aeo_orchestrator.runner import serialize_analytics_result
    from aeo_orchestrator.state import initial_state

    state = initial_state(task_id="ser-analytics", platform="amazon", sku="SER-001")
    state["analytics"] = {
        "daily_summary": "GMV $1000",
        "weekly_trend": "Up 5%",
        "strategy_suggestions": [],
        "kpi_targets": {},
        "report": "Test report",
    }

    serialized = serialize_analytics_result(state)
    assert serialized["task_id"] == "ser-analytics"
    assert serialized["sku"] == "SER-001"
    assert serialized["analytics"]["daily_summary"] == "GMV $1000"


def test_analytics_agent_in_graph_catalog() -> None:
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "analytics" in catalog
