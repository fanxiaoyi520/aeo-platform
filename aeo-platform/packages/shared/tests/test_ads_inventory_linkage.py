"""Tests for MV3-07: Ads-inventory linkage strategy engine."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from aeo_shared.ads_inventory_linkage import (
    AdsInventoryLinkage,
    LinkageRecommendation,
    StockStatus,
)


class TestStockStatus:
    def test_stock_status_values(self) -> None:
        assert StockStatus.CRITICAL.value == "critical"
        assert StockStatus.LOW.value == "low"
        assert StockStatus.HEALTHY.value == "healthy"
        assert StockStatus.OVERSTOCK.value == "overstock"


class TestLinkageRecommendationModel:
    def test_create_recommendation(self) -> None:
        rec = LinkageRecommendation(
            campaign_id="camp-001",
            sku="SKU-001",
            stock_status=StockStatus.LOW,
            current_budget=Decimal("20.00"),
            suggested_budget=Decimal("10.00"),
            budget_change_percent=-50.0,
            reason="Low stock, reduce ad spend to conserve capital",
            urgency="high",
        )
        assert rec.campaign_id == "camp-001"
        assert rec.sku == "SKU-001"
        assert rec.budget_change_percent == -50.0
        assert rec.urgency == "high"


class TestAdsInventoryLinkage:
    @pytest.fixture
    def linkage(self) -> AdsInventoryLinkage:
        return AdsInventoryLinkage()

    @pytest.fixture
    def sample_campaigns(self) -> list[dict[str, Any]]:
        return [
            {
                "campaign_id": "camp-001",
                "sku": "SKU-001",
                "status": "enabled",
                "daily_budget": Decimal("20.00"),
            },
            {
                "campaign_id": "camp-002",
                "sku": "SKU-002",
                "status": "enabled",
                "daily_budget": Decimal("30.00"),
            },
            {
                "campaign_id": "camp-003",
                "sku": "SKU-003",
                "status": "enabled",
                "daily_budget": Decimal("15.00"),
            },
        ]

    @pytest.fixture
    def sample_snapshots(self) -> list[dict[str, Any]]:
        return [
            {
                "campaign_id": "camp-001",
                "spend": Decimal("18.00"),
                "attributed_gmv": Decimal("90.00"),
            },
            {
                "campaign_id": "camp-002",
                "spend": Decimal("25.00"),
                "attributed_gmv": Decimal("175.00"),
            },
            {
                "campaign_id": "camp-003",
                "spend": Decimal("12.00"),
                "attributed_gmv": Decimal("48.00"),
            },
        ]

    @pytest.fixture
    def sample_inventory(self) -> list[dict[str, Any]]:
        return [
            {"sku": "SKU-001", "available_quantity": 8, "inbound_quantity": 0},
            {"sku": "SKU-002", "available_quantity": 120, "inbound_quantity": 50},
            {"sku": "SKU-003", "available_quantity": 35, "inbound_quantity": 0},
        ]

    def test_analyze_returns_recommendations_for_all_campaigns(
        self,
        linkage: AdsInventoryLinkage,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
        sample_inventory: list[dict[str, Any]],
    ) -> None:
        recs = linkage.analyze(sample_campaigns, sample_snapshots, sample_inventory)
        assert len(recs) == 3
        campaign_ids = [r.campaign_id for r in recs]
        assert "camp-001" in campaign_ids
        assert "camp-002" in campaign_ids
        assert "camp-003" in campaign_ids

    def test_critical_stock_reduces_budget(
        self,
        linkage: AdsInventoryLinkage,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
        sample_inventory: list[dict[str, Any]],
    ) -> None:
        recs = linkage.analyze(sample_campaigns, sample_snapshots, sample_inventory)
        camp_001 = next(r for r in recs if r.campaign_id == "camp-001")
        assert camp_001.stock_status == StockStatus.CRITICAL
        assert camp_001.budget_change_percent < 0
        assert camp_001.suggested_budget < camp_001.current_budget

    def test_overstock_increases_budget(
        self,
        linkage: AdsInventoryLinkage,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
        sample_inventory: list[dict[str, Any]],
    ) -> None:
        recs = linkage.analyze(sample_campaigns, sample_snapshots, sample_inventory)
        camp_002 = next(r for r in recs if r.campaign_id == "camp-002")
        assert camp_002.stock_status == StockStatus.OVERSTOCK
        assert camp_002.budget_change_percent > 0
        assert camp_002.suggested_budget > camp_002.current_budget

    def test_healthy_stock_moderate_change(
        self,
        linkage: AdsInventoryLinkage,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
        sample_inventory: list[dict[str, Any]],
    ) -> None:
        recs = linkage.analyze(sample_campaigns, sample_snapshots, sample_inventory)
        camp_003 = next(r for r in recs if r.campaign_id == "camp-003")
        assert camp_003.stock_status == StockStatus.HEALTHY

    def test_missing_inventory_defaults_to_healthy(
        self,
        linkage: AdsInventoryLinkage,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
    ) -> None:
        inventory: list[dict[str, Any]] = []
        recs = linkage.analyze(sample_campaigns, sample_snapshots, inventory)
        assert len(recs) == 3
        for rec in recs:
            assert rec.stock_status == StockStatus.HEALTHY

    def test_skips_disabled_campaigns(
        self,
        linkage: AdsInventoryLinkage,
        sample_snapshots: list[dict[str, Any]],
        sample_inventory: list[dict[str, Any]],
    ) -> None:
        campaigns: list[dict[str, Any]] = [
            {
                "campaign_id": "camp-disabled",
                "sku": "SKU-001",
                "status": "paused",
                "daily_budget": Decimal("20.00"),
            },
        ]
        recs = linkage.analyze(campaigns, sample_snapshots, sample_inventory)
        assert len(recs) == 0

    def test_urgency_levels(
        self,
        linkage: AdsInventoryLinkage,
        sample_snapshots: list[dict[str, Any]],
        sample_inventory: list[dict[str, Any]],
    ) -> None:
        campaigns: list[dict[str, Any]] = [
            {
                "campaign_id": "camp-critical",
                "sku": "SKU-CRIT",
                "status": "enabled",
                "daily_budget": Decimal("20.00"),
            },
            {
                "campaign_id": "camp-over",
                "sku": "SKU-OVER",
                "status": "enabled",
                "daily_budget": Decimal("20.00"),
            },
        ]
        inventory = [
            {"sku": "SKU-CRIT", "available_quantity": 3, "inbound_quantity": 0},
            {"sku": "SKU-OVER", "available_quantity": 200, "inbound_quantity": 0},
        ]
        recs = linkage.analyze(campaigns, sample_snapshots, inventory)
        critical_rec = next(r for r in recs if r.campaign_id == "camp-critical")
        overstock_rec = next(r for r in recs if r.campaign_id == "camp-over")
        assert critical_rec.urgency == "high"
        assert overstock_rec.urgency == "medium"


class TestAdsInventoryLinkageIntegration:
    def test_linkage_with_mock_data(self) -> None:
        from aeo_integrations.amazon.advertising import get_advertising_client
        from aeo_integrations.amazon.inventory import get_inventory_client

        linkage = AdsInventoryLinkage()
        ads_client = get_advertising_client()
        inv_client = get_inventory_client()

        campaigns = [c.model_dump() for c in ads_client.list_campaigns()]
        snapshots = [s.model_dump() for s in ads_client.list_spend_snapshots()]
        inventory = [i.model_dump() for i in inv_client.list_inventory()]

        for camp in campaigns:
            camp.setdefault("sku", f"SKU-{camp['campaign_id']}")

        recs = linkage.analyze(campaigns, snapshots, inventory)
        assert len(recs) >= 1
        for rec in recs:
            assert rec.campaign_id
            assert rec.suggested_budget >= 0
