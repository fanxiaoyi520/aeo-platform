"""Tests for MV3-03: Budget allocation + ROI projection engine."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from aeo_shared.budget_optimizer import (
    BudgetAllocation,
    BudgetOptimizer,
    ROIProjection,
    WhatIfResult,
)


class TestBudgetAllocationModel:
    def test_create_allocation(self) -> None:
        alloc = BudgetAllocation(
            campaign_id="camp-001",
            current_budget=Decimal("15.00"),
            suggested_budget=Decimal("20.00"),
            change_percent=33.3,
            reason="Low ACoS, room for scaling",
        )
        assert alloc.campaign_id == "camp-001"
        assert alloc.suggested_budget == Decimal("20.00")
        assert alloc.change_percent == 33.3


class TestROIProjectionModel:
    def test_create_projection(self) -> None:
        proj = ROIProjection(
            campaign_id="camp-001",
            projection_days=7,
            estimated_spend=Decimal("105.00"),
            estimated_gmv=Decimal("420.00"),
            estimated_roi=4.0,
            confidence=0.75,
        )
        assert proj.campaign_id == "camp-001"
        assert proj.estimated_roi == 4.0
        assert proj.confidence == 0.75


class TestWhatIfResultModel:
    def test_create_what_if(self) -> None:
        result = WhatIfResult(
            campaign_id="camp-001",
            budget_change_percent=50.0,
            current_spend=Decimal("50.00"),
            projected_spend=Decimal("75.00"),
            projected_gmv_change_percent=25.0,
            projected_acos_change=-2.5,
        )
        assert result.budget_change_percent == 50.0
        assert result.projected_gmv_change_percent == 25.0


class TestBudgetOptimizer:
    @pytest.fixture
    def optimizer(self) -> BudgetOptimizer:
        return BudgetOptimizer()

    @pytest.fixture
    def sample_campaigns(self) -> list[dict[str, Any]]:
        return [
            {
                "campaign_id": "camp-001",
                "name": "Kettle Push",
                "status": "enabled",
                "daily_budget": Decimal("15.00"),
            },
            {
                "campaign_id": "camp-002",
                "name": "AirFryer Brand",
                "status": "enabled",
                "daily_budget": Decimal("25.00"),
            },
            {
                "campaign_id": "camp-003",
                "name": "Blender Display",
                "status": "paused",
                "daily_budget": Decimal("10.00"),
            },
        ]

    @pytest.fixture
    def sample_snapshots(self) -> list[dict[str, Any]]:
        return [
            {
                "campaign_id": "camp-001",
                "spend": Decimal("12.50"),
                "attributed_gmv": Decimal("149.95"),
                "impressions": 3200,
                "clicks": 85,
            },
            {
                "campaign_id": "camp-001",
                "spend": Decimal("14.80"),
                "attributed_gmv": Decimal("179.90"),
                "impressions": 3800,
                "clicks": 102,
            },
            {
                "campaign_id": "camp-002",
                "spend": Decimal("22.30"),
                "attributed_gmv": Decimal("359.80"),
                "impressions": 8500,
                "clicks": 210,
            },
            {
                "campaign_id": "camp-003",
                "spend": Decimal("8.10"),
                "attributed_gmv": Decimal("59.99"),
                "impressions": 2100,
                "clicks": 45,
            },
        ]

    def test_allocate_budget_returns_allocation_for_enabled(
        self,
        optimizer: BudgetOptimizer,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
    ) -> None:
        allocations = optimizer.allocate_budget(sample_campaigns, sample_snapshots)
        assert len(allocations) >= 2
        camp_ids = [a.campaign_id for a in allocations]
        assert "camp-001" in camp_ids
        assert "camp-002" in camp_ids

    def test_allocate_budget_skips_paused(
        self,
        optimizer: BudgetOptimizer,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
    ) -> None:
        allocations = optimizer.allocate_budget(sample_campaigns, sample_snapshots)
        camp_ids = [a.campaign_id for a in allocations]
        assert "camp-003" not in camp_ids

    def test_allocate_budget_favors_low_acos(
        self,
        optimizer: BudgetOptimizer,
        sample_campaigns: list[dict[str, Any]],
        sample_snapshots: list[dict[str, Any]],
    ) -> None:
        allocations = optimizer.allocate_budget(sample_campaigns, sample_snapshots)
        camp_001 = next(a for a in allocations if a.campaign_id == "camp-001")
        camp_002 = next(a for a in allocations if a.campaign_id == "camp-002")
        assert camp_001.suggested_budget > camp_001.current_budget
        assert camp_002.change_percent > 0

    def test_project_roi_returns_projection(
        self, optimizer: BudgetOptimizer, sample_snapshots: list[dict[str, Any]]
    ) -> None:
        projection = optimizer.project_roi("camp-001", sample_snapshots, days=7)
        assert projection.campaign_id == "camp-001"
        assert projection.projection_days == 7
        assert projection.estimated_spend > 0
        assert projection.estimated_gmv > 0
        assert projection.estimated_roi > 0
        assert 0 <= projection.confidence <= 1

    def test_project_roi_unknown_campaign(
        self, optimizer: BudgetOptimizer, sample_snapshots: list[dict[str, Any]]
    ) -> None:
        projection = optimizer.project_roi("camp-unknown", sample_snapshots, days=7)
        assert projection.estimated_spend == 0
        assert projection.estimated_gmv == 0

    def test_simulate_budget_increase(
        self, optimizer: BudgetOptimizer, sample_snapshots: list[dict[str, Any]]
    ) -> None:
        result = optimizer.simulate_what_if(
            "camp-001",
            sample_snapshots,
            budget_change_percent=50.0,
        )
        assert result.campaign_id == "camp-001"
        assert result.budget_change_percent == 50.0
        assert result.projected_spend > result.current_spend
        assert result.projected_gmv_change_percent > 0

    def test_simulate_budget_decrease(
        self, optimizer: BudgetOptimizer, sample_snapshots: list[dict[str, Any]]
    ) -> None:
        result = optimizer.simulate_what_if(
            "camp-001",
            sample_snapshots,
            budget_change_percent=-25.0,
        )
        assert result.budget_change_percent == -25.0
        assert result.projected_spend < result.current_spend

    def test_simulate_unknown_campaign(
        self, optimizer: BudgetOptimizer, sample_snapshots: list[dict[str, Any]]
    ) -> None:
        result = optimizer.simulate_what_if(
            "camp-unknown",
            sample_snapshots,
            budget_change_percent=50.0,
        )
        assert result.current_spend == 0
        assert result.projected_spend == 0


class TestBudgetOptimizerIntegration:
    def test_optimizer_with_real_mock_data(self) -> None:
        from aeo_integrations.amazon.advertising import get_advertising_client

        optimizer = BudgetOptimizer()
        client = get_advertising_client()
        campaigns = [c.model_dump() for c in client.list_campaigns()]
        snapshots = [s.model_dump() for s in client.list_spend_snapshots()]

        allocations = optimizer.allocate_budget(campaigns, snapshots)
        assert len(allocations) >= 1

        for alloc in allocations:
            projection = optimizer.project_roi(alloc.campaign_id, snapshots, days=7)
            assert projection.estimated_roi > 0

            what_if = optimizer.simulate_what_if(
                alloc.campaign_id, snapshots, budget_change_percent=20.0
            )
            assert what_if.projected_spend > 0
