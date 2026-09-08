"""P3-04 acceptance tests — DTC Operations Agent end-to-end."""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_dtc_operations_agent_active_in_registry() -> None:
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    agent = registry.get("dtc_operations_agent")
    assert agent.status == "active"
    assert agent.graph_node is None
    assert agent.category.value == "A04"
    capability_names = [c.name for c in agent.capabilities]
    assert "dtc_ops.monitor" in capability_names
    assert "dtc_ops.suggest" in capability_names
    assert agent.platforms == ["shopify"]


def test_dtc_ops_subgraph_registered() -> None:
    from aeo_shared import get_subgraph

    graph = get_subgraph("dtc_ops")
    assert graph.graph_id == "dtc_ops"
    assert "dtc_operations_agent" in graph.agent_ids


def test_dtc_ops_graph_builds() -> None:
    from aeo_orchestrator.graph import build_dtc_ops_graph

    graph = build_dtc_ops_graph()
    assert graph is not None


def test_calculate_dtc_health() -> None:
    from aeo_orchestrator.nodes.dtc_operations import calculate_dtc_health

    metrics = [
        {
            "sessions": 1000,
            "orders": 50,
            "revenue": Decimal("2500.00"),
            "conversion_rate": Decimal("0.05"),
            "cart_abandonment_rate": Decimal("0.65"),
            "avg_order_value": Decimal("50.00"),
        },
        {
            "sessions": 1200,
            "orders": 60,
            "revenue": Decimal("3000.00"),
            "conversion_rate": Decimal("0.05"),
            "cart_abandonment_rate": Decimal("0.60"),
            "avg_order_value": Decimal("50.00"),
        },
    ]
    carts = [
        {"total_value": Decimal("120.00"), "recovery_email_sent": False},
        {"total_value": Decimal("80.00"), "recovery_email_sent": True},
    ]
    customers = [
        {"total_spent": Decimal("500.00"), "accepts_marketing": True},
        {"total_spent": Decimal("300.00"), "accepts_marketing": False},
    ]
    discounts = [
        {"is_active": True, "times_used": 15},
        {"is_active": False, "times_used": 5},
    ]

    health = calculate_dtc_health(metrics, carts, customers, discounts)

    assert health["total_sessions"] == 2200
    assert health["total_orders"] == 110
    assert health["total_revenue"] == 5500.0
    assert health["avg_conversion_rate"] == 0.05
    assert health["avg_cart_abandonment_rate"] == 0.625
    assert health["avg_order_value"] == 50.0
    assert health["abandoned_cart_value"] == 200.0
    assert health["unrecovered_cart_count"] == 1
    assert health["total_customers"] == 2
    assert health["marketing_opt_in_rate"] == 0.5
    assert health["avg_customer_lifetime_value"] == 400.0
    assert health["active_discount_count"] == 1
    assert health["total_discount_redemptions"] == 20
    assert health["metric_days"] == 2


@pytest.mark.asyncio
async def test_dtc_ops_graph_e2e() -> None:
    from aeo_orchestrator.graph import build_dtc_ops_graph
    from aeo_orchestrator.state import initial_state

    graph = build_dtc_ops_graph()
    state = initial_state(
        task_id="p3-04-e2e",
        platform="shopify",
        sku="DTC-HEALTH-001",
        product_info={"title": "Organic Tee", "price": 34.99},
    )

    mock_llm_response = json.dumps(
        {
            "inventory_alerts": [
                {"sku": "DTC-HEALTH-001", "level": "warning", "message": "Low stock"},
            ],
            "pricing_suggestions": [],
            "restock_recommendations": [
                {"sku": "DTC-HEALTH-001", "recommended_quantity": 100, "urgency": "medium"},
            ],
            "abandoned_cart_strategy": {
                "recommendation": "Send recovery email with 10% discount",
                "expected_recovery": 0.15,
            },
            "report": "Store health is moderate. Focus on cart recovery.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.dtc_operations.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_operations.get_store_client") as mock_store,
    ):
        mock_client = mock_store.return_value
        mock_client.get_store_metrics.return_value = []
        mock_client.list_abandoned_carts.return_value = []
        mock_client.list_customers.return_value = []
        mock_client.list_discount_codes.return_value = []

        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "p3-04-e2e"}})

    dtc_ops = result.get("dtc_ops")
    assert dtc_ops is not None
    assert "health_metrics" in dtc_ops
    assert "inventory_alerts" in dtc_ops
    assert "pricing_suggestions" in dtc_ops
    assert "restock_recommendations" in dtc_ops
    assert "abandoned_cart_strategy" in dtc_ops
    assert "report" in dtc_ops

    assert len(dtc_ops["inventory_alerts"]) == 1
    assert dtc_ops["inventory_alerts"][0]["level"] == "warning"

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "dtc_operations_agent"]
    assert len(agent_events) >= 2
    assert agent_events[0]["status"] == "started"
    assert agent_events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_dtc_ops_node_handles_failure() -> None:
    from aeo_orchestrator.nodes.dtc_operations import dtc_operations_node
    from aeo_orchestrator.state import initial_state

    state = initial_state(
        task_id="p3-04-fail",
        platform="shopify",
        sku="DTC-FAIL-001",
    )

    with patch(
        "aeo_orchestrator.nodes.dtc_operations.get_store_client",
        side_effect=RuntimeError("Shopify unavailable"),
    ):
        result = await dtc_operations_node(state)

    dtc_ops = result["dtc_ops"]
    assert "error" in dtc_ops
    assert "Shopify unavailable" in dtc_ops["error"]
    assert dtc_ops["health_metrics"] == {}


@pytest.mark.asyncio
async def test_run_dtc_ops_task() -> None:
    from aeo_orchestrator.runner import run_dtc_ops_task

    mock_llm_response = json.dumps(
        {
            "inventory_alerts": [],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "abandoned_cart_strategy": {},
            "report": "All clear",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.dtc_operations.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_operations.get_store_client") as mock_store,
    ):
        mock_client = mock_store.return_value
        mock_client.get_store_metrics.return_value = []
        mock_client.list_abandoned_carts.return_value = []
        mock_client.list_customers.return_value = []
        mock_client.list_discount_codes.return_value = []

        result = await run_dtc_ops_task(
            sku="DTC-RUN-001",
            platform="shopify",
            product_info={"title": "Test", "price": 19.99},
            task_id="runner-dtc-ops-1",
        )

    assert result["task_id"] == "runner-dtc-ops-1"
    assert result["dtc_ops"] is not None


def test_serialize_dtc_ops_result() -> None:
    from aeo_orchestrator.runner import serialize_dtc_ops_result
    from aeo_orchestrator.state import initial_state

    state = initial_state(task_id="ser-dtc-ops", platform="shopify", sku="DTC-SER-001")
    state["dtc_ops"] = {
        "health_metrics": {"total_orders": 42},
        "inventory_alerts": [],
        "pricing_suggestions": [],
        "restock_recommendations": [],
        "abandoned_cart_strategy": {},
        "report": "Summary",
    }

    serialized = serialize_dtc_ops_result(state)
    assert serialized["task_id"] == "ser-dtc-ops"
    assert serialized["sku"] == "DTC-SER-001"
    assert serialized["platform"] == "shopify"
    assert serialized["dtc_ops"]["health_metrics"]["total_orders"] == 42


def test_dtc_ops_agent_in_graph_catalog() -> None:
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "dtc_ops" in catalog


def test_dtc_operations_node_importable() -> None:
    from aeo_orchestrator.nodes import dtc_operations_node

    assert callable(dtc_operations_node)
