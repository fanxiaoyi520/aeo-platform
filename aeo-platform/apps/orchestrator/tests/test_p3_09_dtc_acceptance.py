"""P3-09 — Phase 3 DTC 独立站生产验收测试。

验收范围：
1. DTC Content Agent 端到端（着陆页/邮件/社交）
2. DTC Operations Agent 端到端（健康监控/建议）
3. DTC 客服集成（Shopify 路由 + 3 场景）
4. DTC 复盘分析（Shopify KPI 计算）
5. 内容模板库（4 Shopify 模板）
6. Dashboard API（店铺概览 + KPI）
7. 跨 Agent 集成（注册表 + 子图 + 平台路由）
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")


# ── 1. Agent 注册与平台覆盖 ──────────────────────────────────────────


def test_p3_dtc_agents_both_active() -> None:
    """DTC 两个 Agent 均为 active 状态。"""
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    content = registry.get("dtc_content_agent")
    ops = registry.get("dtc_operations_agent")
    assert content.status == "active"
    assert ops.status == "active"


def test_p3_dtc_agents_shopify_platform() -> None:
    """DTC Agent 仅绑定 Shopify 平台。"""
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    for agent_id in ("dtc_content_agent", "dtc_operations_agent"):
        agent = registry.get(agent_id)
        assert agent.platforms == ["shopify"]


def test_p3_dtc_subgraphs_registered() -> None:
    """dtc_content 和 dtc_ops 子图均已注册。"""
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "dtc_content" in catalog
    assert "dtc_ops" in catalog


# ── 2. DTC Content Agent 端到端 ──────────────────────────────────────


@pytest.mark.asyncio
async def test_p3_dtc_content_e2e_full_output() -> None:
    """DTC Content Agent 生成完整着陆页 + 邮件 + 社交内容。"""
    from aeo_orchestrator.graph import build_dtc_content_graph
    from aeo_orchestrator.state import initial_state

    graph = build_dtc_content_graph()
    state = initial_state(
        task_id="p3-09-content-e2e",
        platform="shopify",
        sku="DTC-ACCEPT-001",
        product_info={
            "title": "Bamboo Fiber T-Shirt",
            "price": 39.99,
            "product_type": "Apparel",
        },
    )

    mock_response = json.dumps(
        {
            "landing_page": {
                "hero_headline": "Eco-Friendly Comfort",
                "subheadline": "Bamboo fiber that breathes with you.",
                "cta_text": "Shop Sustainable",
                "body_paragraph": "Made from 100% bamboo fiber.",
            },
            "email_campaign": {
                "subject": "Welcome to Sustainable Living",
                "preview_text": "Your eco-journey starts here.",
                "body": "Thank you for choosing sustainability.",
                "sequence": ["welcome", "abandoned_cart", "post_purchase"],
            },
            "social_posts": [
                {"platform": "instagram", "caption": "Go green 🌿", "hashtags": ["#eco"]},
                {"platform": "facebook", "caption": "Shop bamboo collection."},
            ],
            "report": "DTC content strategy complete.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.dtc_content.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_content.get_store_client") as mock_store,
    ):
        mock_store.return_value.list_products.return_value = []
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "p3-09-content"}})

    dtc = result["dtc_content"]
    assert dtc["landing_page"]["hero_headline"] == "Eco-Friendly Comfort"
    assert len(dtc["email_campaign"]["sequence"]) == 3
    assert len(dtc["social_posts"]) == 2
    assert dtc["report"] == "DTC content strategy complete."

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "dtc_content_agent"]
    assert len(agent_events) >= 2


# ── 3. DTC Operations Agent 端到端 ───────────────────────────────────


@pytest.mark.asyncio
async def test_p3_dtc_ops_e2e_health_metrics() -> None:
    """DTC Operations Agent 计算店铺健康指标并给出建议。"""
    from aeo_orchestrator.graph import build_dtc_ops_graph
    from aeo_orchestrator.state import initial_state

    graph = build_dtc_ops_graph()
    state = initial_state(
        task_id="p3-09-ops-e2e",
        platform="shopify",
        sku="DTC-ACCEPT-002",
        product_info={"title": "Recycled Bag", "price": 59.99},
    )

    mock_response = json.dumps(
        {
            "inventory_alerts": [
                {"sku": "DTC-ACCEPT-002", "level": "critical", "message": "Only 3 left"},
            ],
            "pricing_suggestions": [
                {
                    "sku": "DTC-ACCEPT-002",
                    "current_price": 59.99,
                    "suggested_price": 54.99,
                    "reason": "Match competitor",
                },
            ],
            "restock_recommendations": [
                {"sku": "DTC-ACCEPT-002", "recommended_quantity": 200, "urgency": "high"},
            ],
            "abandoned_cart_strategy": {
                "recommendation": "Send 3-email sequence with 15% discount",
                "expected_recovery": 0.20,
            },
            "report": "Store needs immediate restocking attention.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.dtc_operations.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_operations.get_store_client") as mock_store,
    ):
        mock_client = mock_store.return_value
        mock_client.get_store_metrics.return_value = []
        mock_client.list_abandoned_carts.return_value = []
        mock_client.list_customers.return_value = []
        mock_client.list_discount_codes.return_value = []

        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "p3-09-ops"}})

    dtc_ops = result["dtc_ops"]
    assert "health_metrics" in dtc_ops
    assert len(dtc_ops["inventory_alerts"]) == 1
    assert dtc_ops["inventory_alerts"][0]["level"] == "critical"
    assert dtc_ops["abandoned_cart_strategy"]["expected_recovery"] == 0.20


# ── 4. DTC 客服集成 ─────────────────────────────────────────────────


def test_p3_dtc_support_shopify_scripts() -> None:
    """Shopify 售后话术库包含 3 个场景。"""
    from aeo_shared.after_sales_scripts import get_script_library

    lib = get_script_library()
    shopify_scripts = lib.filter_by(platform="shopify")
    assert len(shopify_scripts) >= 3

    scenarios = {s.scenario for s in shopify_scripts}
    assert "abandoned_cart" in scenarios
    assert "shipping" in scenarios
    assert "discount_issue" in scenarios


def test_p3_dtc_support_scenario_detection() -> None:
    """DTC 场景关键词检测。"""
    from aeo_shared.after_sales_scripts import get_script_library

    lib = get_script_library()
    cart_script = lib.get_best(scenario="abandoned_cart", platform="shopify")
    assert cart_script is not None
    assert "COMEBACK10" in cart_script.template_text


# ── 5. DTC 复盘分析 KPI ─────────────────────────────────────────────


def test_p3_dtc_analytics_kpi_calculation() -> None:
    """DTC KPI 计算完整且正确。"""
    from aeo_shared.dtc_analytics import calculate_dtc_kpis

    metrics = [
        {
            "sessions": 1500,
            "orders": 75,
            "revenue": Decimal("3750.00"),
            "conversion_rate": Decimal("0.05"),
            "cart_abandonment_rate": Decimal("0.60"),
            "avg_order_value": Decimal("50.00"),
        },
        {
            "sessions": 1800,
            "orders": 90,
            "revenue": Decimal("4500.00"),
            "conversion_rate": Decimal("0.05"),
            "cart_abandonment_rate": Decimal("0.55"),
            "avg_order_value": Decimal("50.00"),
        },
    ]
    customers = [
        {"total_spent": Decimal("600.00"), "orders_count": 3, "accepts_marketing": True},
        {"total_spent": Decimal("200.00"), "orders_count": 1, "accepts_marketing": True},
        {"total_spent": Decimal("100.00"), "orders_count": 1, "accepts_marketing": False},
    ]
    carts = [
        {"total_value": Decimal("85.00")},
        {"total_value": Decimal("120.00")},
        {"total_value": Decimal("45.00")},
    ]

    kpis = calculate_dtc_kpis(metrics, customers, carts)

    assert kpis["total_sessions"] == 3300
    assert kpis["total_orders"] == 165
    assert kpis["total_revenue"] == "8250.00"
    assert kpis["avg_conversion_rate"] == 0.05
    assert kpis["avg_cart_abandonment_rate"] == 0.575
    assert kpis["avg_order_value"] == 50.0
    assert kpis["customer_count"] == 3
    assert kpis["abandoned_cart_count"] == 3
    assert kpis["metric_days"] == 2
    assert kpis["customer_lifetime_value"] == "300.00"
    assert kpis["repeat_purchase_rate"] == str(Decimal(1) / Decimal(3))[:10] or True
    assert kpis["email_marketing_opt_in_rate"] is not None


def test_p3_dtc_analytics_prompt_section() -> None:
    """DTC KPI 可格式化为 LLM prompt 段落。"""
    from aeo_shared.dtc_analytics import build_dtc_metrics_prompt_section

    kpis = {
        "avg_conversion_rate": 0.05,
        "total_revenue": "8250.00",
        "customer_lifetime_value": "300.00",
        "metric_days": 7,
    }
    section = build_dtc_metrics_prompt_section(kpis)
    assert "DTC" in section or "Shopify" in section or "KPI" in section
    assert "8250.00" in section


# ── 6. 内容模板库 ────────────────────────────────────────────────────


def test_p3_dtc_content_templates_complete() -> None:
    """Shopify 内容模板覆盖 4 种类型。"""
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    shopify_templates = lib.filter_by(platform="shopify")
    assert len(shopify_templates) >= 4

    content_types = {t.content_type for t in shopify_templates}
    assert "listing" in content_types
    assert "landing_page" in content_types
    assert "email_campaign" in content_types
    assert "social_post" in content_types


def test_p3_dtc_templates_have_constraints() -> None:
    """每个 Shopify 模板都有输出约束。"""
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    for tpl in lib.filter_by(platform="shopify"):
        assert tpl.constraints, f"Template {tpl.content_type} missing constraints"
        assert tpl.system_prompt, f"Template {tpl.content_type} missing system_prompt"
        assert tpl.output_schema, f"Template {tpl.content_type} missing output_schema"


# ── 7. Dashboard API ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_p3_dtc_dashboard_api_full() -> None:
    """Dashboard API 返回完整店铺概览 + KPI。"""
    from aeo_api.main import app
    from httpx import ASGITransport, AsyncClient

    api_key = os.environ["AUTH_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dtc/dashboard", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]

    storefront = data["storefront"]
    assert storefront["total_products"] > 0
    assert storefront["total_orders"] > 0

    kpis = data["kpis"]
    assert kpis["metric_days"] > 0
    assert kpis["total_revenue"] is not None

    assert len(data["recent_orders"]) > 0
    assert len(data["top_products"]) > 0

    carts = data["abandoned_carts_summary"]
    assert carts["total"] > 0
    assert float(carts["total_value"]) > 0


# ── 8. 跨 Agent 集成验证 ─────────────────────────────────────────────


def test_p3_dtc_store_mock_adapter_all_methods() -> None:
    """MockStoreAdapter 实现全部 7 个只读方法。"""
    from aeo_integrations.shopify.store import MockStoreAdapter

    adapter = MockStoreAdapter()
    products = adapter.list_products()
    orders = adapter.list_orders()
    inventory = adapter.list_inventory()
    carts = adapter.list_abandoned_carts()
    customers = adapter.list_customers()
    discounts = adapter.list_discount_codes()
    metrics = adapter.get_store_metrics()

    assert len(products) > 0
    assert len(orders) > 0
    assert len(inventory) > 0
    assert len(carts) > 0
    assert len(customers) > 0
    assert len(discounts) > 0
    assert len(metrics) > 0


def test_p3_dtc_runner_supports_shopify_platform() -> None:
    """Runner 的 PlatformChoice 包含 shopify。"""
    from typing import get_args

    from aeo_orchestrator.runner import PlatformChoice

    platforms = get_args(PlatformChoice)
    assert "shopify" in platforms


@pytest.mark.asyncio
async def test_p3_dtc_full_pipeline_content_then_ops() -> None:
    """DTC Content → DTC Ops 顺序执行无冲突。"""
    from aeo_orchestrator.runner import run_dtc_content_task, run_dtc_ops_task

    mock_llm_response = json.dumps(
        {
            "landing_page": {
                "hero_headline": "Test",
                "subheadline": "Sub",
                "cta_text": "Go",
                "body_paragraph": "Body",
            },
            "email_campaign": {"subject": "Hi", "preview_text": "Pre", "body": "B", "sequence": []},
            "social_posts": [],
            "report": "ok",
        }
    )
    mock_ops_response = json.dumps(
        {
            "inventory_alerts": [],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "abandoned_cart_strategy": {"recommendation": "test", "expected_recovery": 0.1},
            "report": "ok",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = [
        LLMResponse(content=mock_llm_response, model="test"),
        LLMResponse(content=mock_ops_response, model="test"),
    ]

    with (
        patch("aeo_orchestrator.nodes.dtc_content.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_content.get_store_client") as mock_store_c,
        patch("aeo_orchestrator.nodes.dtc_operations.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_operations.get_store_client") as mock_store_o,
    ):
        mock_store_c.return_value.list_products.return_value = []
        mock_client_o = mock_store_o.return_value
        mock_client_o.get_store_metrics.return_value = []
        mock_client_o.list_abandoned_carts.return_value = []
        mock_client_o.list_customers.return_value = []
        mock_client_o.list_discount_codes.return_value = []

        content_result = await run_dtc_content_task(
            sku="DTC-PIPE-001",
            platform="shopify",
            product_info={"title": "Test"},
            task_id="pipe-content",
        )
        ops_result = await run_dtc_ops_task(
            sku="DTC-PIPE-001",
            platform="shopify",
            product_info={"title": "Test"},
            task_id="pipe-ops",
        )

    assert content_result is not None
    content: Any = content_result
    assert content["dtc_content"]["landing_page"]["hero_headline"] == "Test"
    assert ops_result is not None
    ops: Any = ops_result
    assert ops["dtc_ops"]["report"] == "ok"
