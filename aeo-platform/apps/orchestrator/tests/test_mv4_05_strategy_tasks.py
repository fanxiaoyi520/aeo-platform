"""MV4-05 — analytics_node integration: strategy_suggestions → created_tasks."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


@pytest.mark.asyncio
async def test_analytics_node_creates_tasks_from_strategy() -> None:
    from aeo_orchestrator.graph import build_analytics_graph
    from aeo_orchestrator.state import initial_state

    graph = build_analytics_graph()
    state = initial_state(
        task_id="mv4-05-strategy-test",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={"title": "Electric Kettle", "price": 29.99},
    )

    mock_llm_response = json.dumps(
        {
            "daily_summary": "GMV $1,234 with 42 orders.",
            "weekly_trend": "Revenue up 12%.",
            "strategy_suggestions": [
                {
                    "action": "increase_ad_spend",
                    "sku": "HOMEBREW-KETTLE-1L",
                    "reason": "Strong ROI supports higher ad budget",
                },
                {
                    "action": "restock",
                    "sku": "HOMEBREW-KETTLE-1L",
                    "reason": "Inventory below safety threshold",
                },
            ],
            "kpi_targets": {"daily_gmv_target": 1000, "daily_gmv_actual": 1234, "target_met": True},
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "mv4-05-strategy-test"}}
        )

    analytics = result.get("analytics")
    assert analytics is not None
    assert "created_tasks" in analytics
    created = analytics["created_tasks"]
    assert len(created) == 2
    assert created[0]["agent_id"] == "ads_agent"
    assert created[1]["agent_id"] == "operations_agent"


@pytest.mark.asyncio
async def test_analytics_node_no_suggestions_no_tasks() -> None:
    from aeo_orchestrator.graph import build_analytics_graph
    from aeo_orchestrator.state import initial_state

    graph = build_analytics_graph()
    state = initial_state(
        task_id="mv4-05-empty-test",
        platform="amazon",
        sku="SKU-EMPTY",
    )

    mock_llm_response = json.dumps(
        {
            "daily_summary": "Flat day.",
            "weekly_trend": "No change.",
            "strategy_suggestions": [],
            "kpi_targets": {},
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "mv4-05-empty-test"}}
        )

    analytics = result["analytics"]
    assert analytics["created_tasks"] == []


@pytest.mark.asyncio
async def test_analytics_node_unknown_action_skipped() -> None:
    from aeo_orchestrator.graph import build_analytics_graph
    from aeo_orchestrator.state import initial_state

    graph = build_analytics_graph()
    state = initial_state(
        task_id="mv4-05-unknown-action",
        platform="amazon",
        sku="SKU-001",
    )

    mock_llm_response = json.dumps(
        {
            "daily_summary": "Mixed day.",
            "weekly_trend": "Stable.",
            "strategy_suggestions": [
                {"action": "fly_to_moon", "sku": "SKU-001", "reason": "why not"},
                {"action": "increase_ad_spend", "sku": "SKU-001", "reason": "ROI good"},
            ],
            "kpi_targets": {},
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "mv4-05-unknown-action"}}
        )

    analytics = result["analytics"]
    created = analytics["created_tasks"]
    assert len(created) == 1
    assert created[0]["agent_id"] == "ads_agent"
