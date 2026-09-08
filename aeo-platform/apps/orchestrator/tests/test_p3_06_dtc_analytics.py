"""P3-06 acceptance tests — DTC Analytics Integration."""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_calculate_dtc_kpis_basic() -> None:
    from aeo_shared.dtc_analytics import calculate_dtc_kpis

    metrics = [
        {
            "sessions": 1000,
            "orders": 50,
            "revenue": Decimal("2500.00"),
            "conversion_rate": Decimal("0.05"),
            "cart_abandonment_rate": Decimal("0.65"),
            "avg_order_value": Decimal("50.00"),
        },
    ]
    customers = [
        {"total_spent": Decimal("500.00"), "orders_count": 3, "accepts_marketing": True},
        {"total_spent": Decimal("200.00"), "orders_count": 1, "accepts_marketing": False},
    ]
    carts = [{"cart_id": "C1"}, {"cart_id": "C2"}]

    kpis = calculate_dtc_kpis(metrics, customers, carts)

    assert kpis["avg_conversion_rate"] == 0.05
    assert kpis["avg_cart_abandonment_rate"] == 0.65
    assert kpis["avg_order_value"] == 50.0
    assert kpis["total_revenue"] == "2500.00"
    assert kpis["total_sessions"] == 1000
    assert kpis["total_orders"] == 50
    assert kpis["customer_lifetime_value"] == "350.00"
    assert kpis["repeat_purchase_rate"] == "0.5000"
    assert kpis["email_marketing_opt_in_rate"] == "0.5000"
    assert kpis["metric_days"] == 1
    assert kpis["customer_count"] == 2
    assert kpis["abandoned_cart_count"] == 2


def test_calculate_dtc_kpis_empty() -> None:
    from aeo_shared.dtc_analytics import calculate_dtc_kpis

    kpis = calculate_dtc_kpis([], [], [])
    assert kpis["avg_conversion_rate"] is None
    assert kpis["total_revenue"] == "0"
    assert kpis["total_sessions"] == 0
    assert kpis["customer_lifetime_value"] is None


def test_build_dtc_metrics_prompt_section() -> None:
    from aeo_shared.dtc_analytics import build_dtc_metrics_prompt_section

    kpis = {
        "avg_conversion_rate": 0.05,
        "avg_cart_abandonment_rate": 0.65,
        "avg_order_value": 50.0,
        "total_revenue": "2500.00",
        "customer_lifetime_value": "350.00",
        "repeat_purchase_rate": "0.5000",
        "email_marketing_opt_in_rate": "0.5000",
        "abandoned_cart_count": 2,
        "metric_days": 7,
    }

    section = build_dtc_metrics_prompt_section(kpis)
    assert "DTC Shopify KPIs" in section
    assert "0.05" in section
    assert "2500.00" in section
    assert "350.00" in section


@pytest.mark.asyncio
async def test_analytics_node_shopify_includes_dtc_kpis() -> None:
    from aeo_orchestrator.nodes.analytics import analytics_node
    from aeo_orchestrator.state import initial_state

    state = initial_state(
        task_id="p3-06-shopify",
        platform="shopify",
        sku="DTC-ANALYTICS-001",
        product_info={"title": "Test Product", "price": 29.99},
    )

    mock_llm_response = json.dumps(
        {
            "daily_summary": "DTC store performing well.",
            "weekly_trend": "Revenue up 10%.",
            "strategy_suggestions": [],
            "kpi_targets": {"target_met": True},
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider),
        patch("aeo_integrations.shopify.store.get_store_client") as mock_store,
    ):
        mock_client = mock_store.return_value
        mock_client.get_store_metrics.return_value = []
        mock_client.list_customers.return_value = []
        mock_client.list_abandoned_carts.return_value = []

        result = await analytics_node(state)

    analytics = result["analytics"]
    assert "dtc_kpis" in analytics
    assert isinstance(analytics["dtc_kpis"], dict)


@pytest.mark.asyncio
async def test_analytics_node_amazon_no_dtc_kpis() -> None:
    from aeo_orchestrator.nodes.analytics import analytics_node
    from aeo_orchestrator.state import initial_state

    state = initial_state(
        task_id="p3-06-amazon",
        platform="amazon",
        sku="AMZ-001",
    )

    mock_llm_response = json.dumps(
        {
            "daily_summary": "Amazon performing well.",
            "weekly_trend": "Stable.",
            "strategy_suggestions": [],
            "kpi_targets": {},
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
        result = await analytics_node(state)

    analytics = result["analytics"]
    assert "dtc_kpis" in analytics
    assert analytics["dtc_kpis"] == {}


def test_dtc_analytics_module_importable() -> None:
    from aeo_shared.dtc_analytics import build_dtc_metrics_prompt_section, calculate_dtc_kpis

    assert callable(calculate_dtc_kpis)
    assert callable(build_dtc_metrics_prompt_section)
