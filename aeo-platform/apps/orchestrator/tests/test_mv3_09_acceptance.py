"""MV3-09 acceptance tests — ads + ops + budget + linkage end-to-end."""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def _mock_ads_llm() -> AsyncMock:
    response_body = json.dumps(
        {
            "suggestions": [
                {
                    "campaign_id": "CAMP-001",
                    "type": "bid_increase",
                    "reason": "Low ACoS, room to scale",
                    "suggested_value": "1.50",
                },
                {
                    "campaign_id": "CAMP-002",
                    "type": "bid_decrease",
                    "reason": "High ACoS, reduce spend",
                    "suggested_value": "0.80",
                },
            ],
            "bid_simulation": {
                "campaign_id": "CAMP-001",
                "current_bid": "1.00",
                "suggested_bid": "1.50",
                "estimated_impression_lift": "25%",
                "estimated_gmv_change": "15%",
            },
            "report": "Campaigns show mixed performance. CAMP-001 has strong ROI.",
        }
    )
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=response_body, model="test")
    return mock_provider


def _mock_ops_llm() -> AsyncMock:
    response_body = json.dumps(
        {
            "inventory_alerts": [
                {"sku": "TEST-001", "level": "warning", "message": "Low stock"},
            ],
            "pricing_suggestions": [
                {"sku": "TEST-001", "current_price": "29.99", "suggested_price": "32.99"},
            ],
            "restock_recommendations": [
                {"sku": "TEST-001", "recommended_quantity": 100, "urgency": "high"},
            ],
            "report": "Inventory health needs attention. Restock recommended.",
        }
    )
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=response_body, model="test")
    return mock_provider


@pytest.mark.asyncio
async def test_mv3_09_ads_agent_10_skus_end_to_end() -> None:
    """MV3-09: ads agent runs across 10 SKUs with metrics, suggestions, and trace."""
    from aeo_orchestrator.runner import run_ads_task, serialize_ads_result

    results = []
    for i in range(10):
        mock_provider = _mock_ads_llm()
        with patch("aeo_orchestrator.nodes.ads.get_llm_provider", return_value=mock_provider):
            state = await run_ads_task(
                sku=f"TEST-ADS-{i:03d}",
                platform="amazon",
                market="US",
                task_id=f"mv3-09-ads-{i}",
                product_info={"title": f"Test Product {i}", "price": 29.99},
            )
        serialized = serialize_ads_result(state)
        results.append(serialized)

    assert len(results) == 10

    for i, result in enumerate(results):
        assert result["task_id"] == f"mv3-09-ads-{i}"
        ads = result.get("ads", {})
        assert "metrics" in ads, f"SKU {i}: missing metrics"
        metrics = ads["metrics"]
        assert "total_spend" in metrics
        assert "total_gmv" in metrics
        assert "avg_acos" in metrics
        assert "avg_ctr" in metrics
        assert "campaign_count" in metrics

        assert "suggestions" in ads, f"SKU {i}: missing suggestions"
        assert isinstance(ads["suggestions"], list)

        assert "campaigns" in ads, f"SKU {i}: missing campaigns"
        assert isinstance(ads["campaigns"], list)

        assert "report" in ads, f"SKU {i}: missing report"
        assert isinstance(ads["report"], str)

        trace = result.get("trace", [])
        agent_names = [e.get("agent") for e in trace if isinstance(e, dict)]
        assert "ads_agent" in agent_names, f"SKU {i}: ads_agent not in trace"


@pytest.mark.asyncio
async def test_mv3_09_ops_agent_10_skus_end_to_end() -> None:
    """MV3-09: ops agent runs across 10 SKUs with health metrics and suggestions."""
    from aeo_orchestrator.runner import run_ops_task, serialize_ops_result

    results = []
    for i in range(10):
        mock_provider = _mock_ops_llm()
        with patch(
            "aeo_orchestrator.nodes.operations.get_llm_provider", return_value=mock_provider
        ):
            state = await run_ops_task(
                sku=f"TEST-OPS-{i:03d}",
                platform="amazon",
                market="US",
                task_id=f"mv3-09-ops-{i}",
                product_info={"title": f"Test Product {i}", "price": 19.99},
            )
        serialized = serialize_ops_result(state)
        results.append(serialized)

    assert len(results) == 10

    for i, result in enumerate(results):
        assert result["task_id"] == f"mv3-09-ops-{i}"
        ops = result.get("ops", {})
        assert "health_metrics" in ops, f"SKU {i}: missing health_metrics"
        health = ops["health_metrics"]
        assert "total_available" in health
        assert "low_stock_count" in health
        assert "item_count" in health

        assert "seller_central_inspection" in ops, f"SKU {i}: missing inspection"

        assert "report" in ops, f"SKU {i}: missing report"
        assert isinstance(ops["report"], str)

        trace = result.get("trace", [])
        agent_names = [e.get("agent") for e in trace if isinstance(e, dict)]
        assert "operations_agent" in agent_names, f"SKU {i}: operations_agent not in trace"


def test_mv3_09_budget_optimizer_end_to_end() -> None:
    """MV3-09: BudgetOptimizer allocate -> project -> simulate chain."""
    from aeo_shared.budget_optimizer import BudgetOptimizer

    optimizer = BudgetOptimizer()

    campaigns = [
        {"campaign_id": "CAMP-001", "status": "enabled", "daily_budget": Decimal("50")},
        {"campaign_id": "CAMP-002", "status": "enabled", "daily_budget": Decimal("30")},
        {"campaign_id": "CAMP-003", "status": "enabled", "daily_budget": Decimal("40")},
        {"campaign_id": "CAMP-004", "status": "paused", "daily_budget": Decimal("20")},
    ]
    snapshots = [
        {"campaign_id": "CAMP-001", "spend": Decimal("100"), "attributed_gmv": Decimal("500")},
        {"campaign_id": "CAMP-001", "spend": Decimal("120"), "attributed_gmv": Decimal("600")},
        {"campaign_id": "CAMP-002", "spend": Decimal("80"), "attributed_gmv": Decimal("200")},
        {"campaign_id": "CAMP-002", "spend": Decimal("90"), "attributed_gmv": Decimal("250")},
        {"campaign_id": "CAMP-003", "spend": Decimal("60"), "attributed_gmv": Decimal("300")},
        {"campaign_id": "CAMP-003", "spend": Decimal("70"), "attributed_gmv": Decimal("350")},
    ]

    allocations = optimizer.allocate_budget(campaigns, snapshots)
    assert len(allocations) == 3
    for alloc in allocations:
        assert alloc.campaign_id in ("CAMP-001", "CAMP-002", "CAMP-003")
        assert alloc.suggested_budget > 0
        assert alloc.change_percent != 0

    camp001_alloc = next(a for a in allocations if a.campaign_id == "CAMP-001")
    camp002_alloc = next(a for a in allocations if a.campaign_id == "CAMP-002")
    assert camp001_alloc.change_percent > camp002_alloc.change_percent, (
        "Lower ACoS campaign should get more budget increase"
    )

    projection = optimizer.project_roi("CAMP-001", snapshots, days=14)
    assert projection.campaign_id == "CAMP-001"
    assert projection.projection_days == 14
    assert projection.estimated_spend > 0
    assert projection.estimated_gmv > 0
    assert 0 < projection.confidence <= 1.0

    what_if = optimizer.simulate_what_if("CAMP-001", snapshots, budget_change_percent=20)
    assert what_if.campaign_id == "CAMP-001"
    assert what_if.budget_change_percent == 20
    assert what_if.projected_spend > what_if.current_spend


def test_mv3_09_ads_inventory_linkage() -> None:
    """MV3-09: stock status drives budget adjustments."""
    from aeo_shared.ads_inventory_linkage import AdsInventoryLinkage, StockStatus

    linkage = AdsInventoryLinkage()

    campaigns = [
        {
            "campaign_id": "CAMP-001",
            "status": "enabled",
            "sku": "SKU-CRITICAL",
            "daily_budget": Decimal("50"),
        },
        {
            "campaign_id": "CAMP-002",
            "status": "enabled",
            "sku": "SKU-LOW",
            "daily_budget": Decimal("40"),
        },
        {
            "campaign_id": "CAMP-003",
            "status": "enabled",
            "sku": "SKU-HEALTHY",
            "daily_budget": Decimal("30"),
        },
        {
            "campaign_id": "CAMP-004",
            "status": "enabled",
            "sku": "SKU-OVERSTOCK",
            "daily_budget": Decimal("20"),
        },
    ]
    snapshots = [
        {"campaign_id": "CAMP-001", "spend": Decimal("100")},
        {"campaign_id": "CAMP-002", "spend": Decimal("80")},
        {"campaign_id": "CAMP-003", "spend": Decimal("60")},
        {"campaign_id": "CAMP-004", "spend": Decimal("40")},
    ]
    inventory = [
        {"sku": "SKU-CRITICAL", "available_quantity": 5},
        {"sku": "SKU-LOW", "available_quantity": 15},
        {"sku": "SKU-HEALTHY", "available_quantity": 50},
        {"sku": "SKU-OVERSTOCK", "available_quantity": 150},
    ]

    recommendations = linkage.analyze(campaigns, snapshots, inventory)
    assert len(recommendations) == 4

    rec_map = {r.campaign_id: r for r in recommendations}

    critical_rec = rec_map["CAMP-001"]
    assert critical_rec.stock_status == StockStatus.CRITICAL
    assert critical_rec.budget_change_percent < 0
    assert critical_rec.urgency == "high"

    low_rec = rec_map["CAMP-002"]
    assert low_rec.stock_status == StockStatus.LOW
    assert low_rec.budget_change_percent < 0
    assert low_rec.urgency == "high"

    healthy_rec = rec_map["CAMP-003"]
    assert healthy_rec.stock_status == StockStatus.HEALTHY
    assert healthy_rec.budget_change_percent > 0

    overstock_rec = rec_map["CAMP-004"]
    assert overstock_rec.stock_status == StockStatus.OVERSTOCK
    assert overstock_rec.budget_change_percent > 0
    assert overstock_rec.urgency == "medium"


def test_mv3_09_agent_registry_ads_and_ops_active() -> None:
    """MV3-09: ads_agent and operations_agent are registered as active."""
    from aeo_shared.agent_catalog import get_default_registry

    registry = get_default_registry()
    agents = registry.list_agents(status="active")
    agent_ids = {a.agent_id for a in agents}

    assert "ads_agent" in agent_ids, "ads_agent not found in active agents"
    assert "operations_agent" in agent_ids, "operations_agent not found in active agents"


def test_mv3_09_campaign_metrics_calculation() -> None:
    """MV3-09: campaign metrics are calculated correctly."""
    from aeo_orchestrator.nodes.ads import calculate_campaign_metrics

    campaigns = [
        {"campaign_id": "CAMP-001", "status": "enabled"},
        {"campaign_id": "CAMP-002", "status": "enabled"},
    ]
    snapshots = [
        {
            "campaign_id": "CAMP-001",
            "spend": 100,
            "attributed_gmv": 500,
            "impressions": 1000,
            "clicks": 50,
        },
        {
            "campaign_id": "CAMP-001",
            "spend": 120,
            "attributed_gmv": 600,
            "impressions": 1200,
            "clicks": 60,
        },
        {
            "campaign_id": "CAMP-002",
            "spend": 80,
            "attributed_gmv": 200,
            "impressions": 800,
            "clicks": 30,
        },
    ]

    metrics = calculate_campaign_metrics(campaigns, snapshots)

    assert metrics["total_spend"] == 300.0
    assert metrics["total_gmv"] == 1300.0
    assert metrics["total_impressions"] == 3000
    assert metrics["total_clicks"] == 140
    assert metrics["campaign_count"] == 2
    assert metrics["avg_acos"] == round(300 / 1300 * 100, 2)
    assert metrics["avg_ctr"] == round(140 / 3000 * 100, 2)


def test_mv3_09_inventory_health_calculation() -> None:
    """MV3-09: inventory health metrics are calculated correctly."""
    from aeo_orchestrator.nodes.operations import calculate_inventory_health

    inventory = [
        {
            "sku": "SKU-001",
            "available_quantity": 100,
            "inbound_quantity": 50,
            "reserved_quantity": 10,
        },
        {"sku": "SKU-002", "available_quantity": 15, "inbound_quantity": 0, "reserved_quantity": 5},
        {"sku": "SKU-003", "available_quantity": 8, "inbound_quantity": 20, "reserved_quantity": 2},
    ]

    health = calculate_inventory_health(inventory)

    assert health["total_available"] == 123
    assert health["total_inbound"] == 70
    assert health["total_reserved"] == 17
    assert health["item_count"] == 3
    assert health["low_stock_count"] == 2
    assert len(health["low_stock_items"]) == 2

    low_skus = {item["sku"] for item in health["low_stock_items"]}
    assert "SKU-002" in low_skus
    assert "SKU-003" in low_skus
