"""P7-16/17: Tests for auto-pricing algorithm."""

from __future__ import annotations

import pytest
from aeo_shared.pricing import (
    PricingInputs,
    PricingSuggestion,
    competition_candidate,
    days_of_stock_remaining,
    inventory_candidate,
    roi_floor_price,
    suggest_price,
)


class TestDaysOfStockRemaining:
    def test_zero_velocity_returns_infinity(self) -> None:
        assert days_of_stock_remaining(100, 0) == float("inf")

    def test_negative_velocity_returns_infinity(self) -> None:
        assert days_of_stock_remaining(100, -1) == float("inf")

    def test_normal_calculation(self) -> None:
        assert days_of_stock_remaining(100, 10) == 10.0


class TestCompetitionCandidate:
    def test_undercut_when_more_expensive(self) -> None:
        # Current 20, competitor 15 → undercut to 14.85 (1% below)
        assert competition_candidate(20.0, 15.0) == pytest.approx(14.85)

    def test_capture_half_gap_when_cheaper(self) -> None:
        # Current 10, competitor 12 → capture half the gap → 11
        assert competition_candidate(10.0, 12.0) == pytest.approx(11.0)

    def test_zero_competitor_returns_current(self) -> None:
        assert competition_candidate(10.0, 0.0) == 10.0


class TestInventoryCandidate:
    def test_low_stock_raises_price(self) -> None:
        assert inventory_candidate(100.0, 5) == pytest.approx(105.0)

    def test_healthy_stock_holds_price(self) -> None:
        assert inventory_candidate(100.0, 14) == 100.0

    def test_overstocked_drops_price(self) -> None:
        assert inventory_candidate(100.0, 30) == pytest.approx(95.0)

    def test_infinite_days_returns_current(self) -> None:
        assert inventory_candidate(100.0, float("inf")) == 100.0


class TestRoiFloor:
    def test_twenty_percent_roi(self) -> None:
        assert roi_floor_price(50.0, 0.2) == pytest.approx(60.0)

    def test_zero_roi_returns_cost(self) -> None:
        assert roi_floor_price(50.0, 0.0) == 50.0

    def test_negative_roi_returns_cost(self) -> None:
        assert roi_floor_price(50.0, -0.1) == 50.0


class TestSuggestPrice:
    def test_roi_floor_is_respected(self) -> None:
        inputs = PricingInputs(
            current_price=10.0,
            cost=50.0,
            lowest_competitor_price=55.0,
            stock_on_hand=100,
            daily_sales_velocity=10.0,
            target_roi=0.2,
        )
        result = suggest_price(inputs)
        assert result.suggested_price >= result.roi_floor_price
        assert result.roi_floor_price == pytest.approx(60.0)

    def test_low_stock_raises_price(self) -> None:
        inputs = PricingInputs(
            current_price=100.0,
            cost=40.0,
            lowest_competitor_price=100.0,
            stock_on_hand=5,
            daily_sales_velocity=1.0,  # 5 days remaining
            target_roi=0.1,
        )
        result = suggest_price(inputs)
        assert result.suggested_price >= 100.0
        assert "low stock" in result.reason

    def test_overstocked_drops_price(self) -> None:
        inputs = PricingInputs(
            current_price=100.0,
            cost=40.0,
            lowest_competitor_price=100.0,
            stock_on_hand=1000,
            daily_sales_velocity=10.0,  # 100 days remaining
            target_roi=0.1,
        )
        result = suggest_price(inputs)
        assert result.suggested_price < 100.0
        assert "overstocked" in result.reason

    def test_platform_min_clamps(self) -> None:
        inputs = PricingInputs(
            current_price=1.0,
            cost=0.5,
            lowest_competitor_price=0.1,
            stock_on_hand=1000,
            daily_sales_velocity=10.0,
            target_roi=0.0,
            platform_min_price=0.5,
        )
        result = suggest_price(inputs)
        assert result.suggested_price >= 0.5

    def test_invalid_cost_raises(self) -> None:
        with pytest.raises(ValueError, match="cost"):
            suggest_price(
                PricingInputs(
                    current_price=10.0,
                    cost=0.0,
                    lowest_competitor_price=10.0,
                    stock_on_hand=10,
                    daily_sales_velocity=1.0,
                )
            )

    def test_invalid_current_price_raises(self) -> None:
        with pytest.raises(ValueError, match="current_price"):
            suggest_price(
                PricingInputs(
                    current_price=0.0,
                    cost=5.0,
                    lowest_competitor_price=10.0,
                    stock_on_hand=10,
                    daily_sales_velocity=1.0,
                )
            )

    def test_returns_pricing_suggestion_dataclass(self) -> None:
        inputs = PricingInputs(
            current_price=100.0,
            cost=40.0,
            lowest_competitor_price=95.0,
            stock_on_hand=100,
            daily_sales_velocity=10.0,
            target_roi=0.1,
        )
        result = suggest_price(inputs)
        assert isinstance(result, PricingSuggestion)
        assert result.suggested_price > 0
        assert result.competition_price > 0
        assert result.inventory_price > 0
        assert result.roi_floor_price > 0
        assert result.reason

    def test_competitive_undercut_wins_over_inventory(self) -> None:
        inputs = PricingInputs(
            current_price=100.0,
            cost=40.0,
            lowest_competitor_price=80.0,  # competitor much cheaper
            stock_on_hand=100,
            daily_sales_velocity=10.0,
            target_roi=0.1,
        )
        result = suggest_price(inputs)
        assert result.suggested_price < 100.0
        assert "price competition" in result.reason
