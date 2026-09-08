"""MV3-04 acceptance tests — A04 Operations Agent end-to-end."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_operations_agent_active_in_registry() -> None:
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    agent = registry.get("operations_agent")
    assert agent.status == "active"
    assert agent.graph_node == "ops"
    assert agent.category.value == "A04"
    assert agent.risk_level.value == "L1"
    capability_names = [c.name for c in agent.capabilities]
    assert "ops.monitor" in capability_names
    assert "ops.suggest" in capability_names


def test_ops_subgraph_registered() -> None:
    from aeo_shared import get_subgraph

    graph = get_subgraph("ops")
    assert graph.graph_id == "ops"
    assert "operations_agent" in graph.agent_ids


def test_ops_graph_builds() -> None:
    from aeo_orchestrator.graph import build_ops_graph

    graph = build_ops_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_ops_graph_e2e() -> None:
    from aeo_orchestrator.graph import build_ops_graph
    from aeo_orchestrator.state import initial_state

    graph = build_ops_graph()
    state = initial_state(
        task_id="mv3-04-e2e",
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
            "inventory_alerts": [
                {
                    "sku": "HOMEBREW-VACUUM-S",
                    "level": "warning",
                    "message": "Stock below 50 units, consider restocking",
                }
            ],
            "pricing_suggestions": [
                {
                    "sku": "HOMEBREW-KETTLE-1L",
                    "current_price": 29.99,
                    "suggested_price": 32.99,
                    "reason": "Strong inventory position, room for margin increase",
                }
            ],
            "restock_recommendations": [
                {
                    "sku": "HOMEBREW-VACUUM-S",
                    "recommended_quantity": 100,
                    "urgency": "medium",
                }
            ],
            "report": "Inventory levels are generally healthy. One SKU needs attention.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.operations.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "mv3-04-e2e"}})

    ops = result.get("ops")
    assert ops is not None
    assert "inventory" in ops
    assert "health_metrics" in ops
    assert "inventory_alerts" in ops
    assert "pricing_suggestions" in ops
    assert "restock_recommendations" in ops
    assert "report" in ops

    assert len(ops["inventory"]) >= 1
    assert "low_stock_count" in ops["health_metrics"]
    assert "total_available" in ops["health_metrics"]

    assert isinstance(ops["report"], str)
    assert len(ops["report"]) > 0

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "operations_agent"]
    assert len(agent_events) >= 2
    assert agent_events[0]["status"] == "started"
    assert agent_events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_run_ops_task() -> None:
    from aeo_orchestrator.runner import run_ops_task

    mock_llm_response = json.dumps(
        {
            "inventory_alerts": [],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "report": "All inventory levels healthy.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.operations.get_llm_provider", return_value=mock_provider):
        result = await run_ops_task(
            sku="HOMEBREW-KETTLE-1L",
            product_info={"title": "Electric Kettle", "price": 29.99},
            task_id="runner-ops-1",
        )

    assert result["task_id"] == "runner-ops-1"
    assert result["ops"] is not None


def test_serialize_ops_result() -> None:
    from aeo_orchestrator.runner import serialize_ops_result
    from aeo_orchestrator.state import initial_state

    state = initial_state(task_id="ser-ops", platform="amazon", sku="SER-001")
    state["ops"] = {
        "inventory": [{"sku": "SER-001", "available_quantity": 50}],
        "health_metrics": {"low_stock_count": 0, "total_available": 50},
        "inventory_alerts": [],
        "pricing_suggestions": [],
        "restock_recommendations": [],
        "report": "Test report",
    }

    serialized = serialize_ops_result(state)
    assert serialized["task_id"] == "ser-ops"
    assert serialized["sku"] == "SER-001"
    assert serialized["ops"]["health_metrics"]["total_available"] == 50


def test_ops_node_health_metrics() -> None:
    from aeo_orchestrator.nodes.operations import calculate_inventory_health

    inventory = [
        {"sku": "SKU-1", "available_quantity": 100, "inbound_quantity": 20, "reserved_quantity": 5},
        {"sku": "SKU-2", "available_quantity": 30, "inbound_quantity": 0, "reserved_quantity": 2},
        {"sku": "SKU-3", "available_quantity": 10, "inbound_quantity": 50, "reserved_quantity": 1},
    ]

    health = calculate_inventory_health(inventory, low_stock_threshold=25)

    assert health["total_available"] == 140
    assert health["total_inbound"] == 70
    assert health["total_reserved"] == 8
    assert health["low_stock_count"] == 1
    assert len(health["low_stock_items"]) == 1


def test_operations_agent_in_graph_catalog() -> None:
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "ops" in catalog
    assert "ads" in catalog
    assert "selection" in catalog
