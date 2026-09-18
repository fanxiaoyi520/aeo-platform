"""P7-19: Tests for ad optimization algorithm."""

from __future__ import annotations

from aeo_shared.ad_optimization import (
    AdOptimizer,
    CampaignPerformance,
    CampaignRecommendation,
    OptimizationAction,
    OptimizationRules,
    PortfolioOptimization,
    classify_campaign,
    compute_bid_adjustment,
)


def perf(
    campaign_id: str = "C1",
    ad_spend: float = 100.0,
    sales: float = 400.0,
    current_bid: float = 1.0,
    daily_budget: float = 50.0,
) -> CampaignPerformance:
    return CampaignPerformance(
        campaign_id=campaign_id,
        ad_spend=ad_spend,
        sales=sales,
        current_bid=current_bid,
        daily_budget=daily_budget,
    )


class TestCampaignPerformance:
    def test_acos_calculation(self) -> None:
        assert perf(ad_spend=100, sales=400).acos == 0.25

    def test_acos_zero_sales_returns_infinity(self) -> None:
        assert perf(ad_spend=100, sales=0).acos == float("inf")

    def test_roas_calculation(self) -> None:
        assert perf(ad_spend=100, sales=400).roas == 4.0

    def test_roas_zero_spend_returns_zero(self) -> None:
        assert perf(ad_spend=0, sales=400).roas == 0.0


class TestClassifyCampaign:
    def test_pause_when_acos_above_pause_threshold(self) -> None:
        rules = OptimizationRules()
        assert classify_campaign(0.70, rules) == OptimizationAction.PAUSE

    def test_reduce_when_acos_above_reduce_threshold(self) -> None:
        rules = OptimizationRules()
        assert classify_campaign(0.45, rules) == OptimizationAction.REDUCE

    def test_hold_when_acos_within_band(self) -> None:
        rules = OptimizationRules()
        assert classify_campaign(0.25, rules) == OptimizationAction.HOLD

    def test_boost_when_acos_below_boost_threshold(self) -> None:
        rules = OptimizationRules()
        assert classify_campaign(0.10, rules) == OptimizationAction.BOOST

    def test_infinite_acos_pauses(self) -> None:
        rules = OptimizationRules()
        assert classify_campaign(float("inf"), rules) == OptimizationAction.PAUSE


class TestComputeBidAdjustment:
    def test_boost_scales_with_headroom(self) -> None:
        rules = OptimizationRules()
        suggested, delta = compute_bid_adjustment(1.0, OptimizationAction.BOOST, 0.05, rules)
        assert suggested > 1.0
        assert delta > 0
        assert delta <= rules.max_bid_increase_pct

    def test_reduce_scales_with_overshoot(self) -> None:
        rules = OptimizationRules()
        suggested, delta = compute_bid_adjustment(1.0, OptimizationAction.REDUCE, 0.50, rules)
        assert suggested < 1.0
        assert delta < 0
        assert delta >= -rules.max_bid_decrease_pct

    def test_pause_zeroes_bid(self) -> None:
        rules = OptimizationRules()
        suggested, delta = compute_bid_adjustment(1.0, OptimizationAction.PAUSE, 0.80, rules)
        assert suggested == 0.0
        assert delta == -1.0

    def test_hold_keeps_bid(self) -> None:
        rules = OptimizationRules()
        suggested, delta = compute_bid_adjustment(1.0, OptimizationAction.HOLD, 0.25, rules)
        assert suggested == 1.0
        assert delta == 0.0

    def test_min_bid_floor_enforced(self) -> None:
        rules = OptimizationRules(min_bid=0.10)
        suggested, _ = compute_bid_adjustment(0.12, OptimizationAction.REDUCE, 0.40, rules)
        assert suggested >= 0.10


class TestAdOptimizer:
    def test_recommend_returns_campaign_recommendation(self) -> None:
        optimizer = AdOptimizer()
        rec = optimizer.recommend(perf())
        assert isinstance(rec, CampaignRecommendation)
        assert rec.campaign_id == "C1"
        assert rec.action in OptimizationAction

    def test_recommend_boost_for_low_acos(self) -> None:
        optimizer = AdOptimizer()
        rec = optimizer.recommend(perf(ad_spend=100, sales=1000))  # ACOS 0.10
        assert rec.action == OptimizationAction.BOOST
        assert rec.suggested_bid > rec.current_bid

    def test_recommend_pause_for_high_acos(self) -> None:
        optimizer = AdOptimizer()
        rec = optimizer.recommend(perf(ad_spend=700, sales=1000))  # ACOS 0.70
        assert rec.action == OptimizationAction.PAUSE
        assert rec.suggested_bid == 0.0

    def test_recommend_handles_zero_sales(self) -> None:
        optimizer = AdOptimizer()
        rec = optimizer.recommend(perf(ad_spend=100, sales=0))
        assert rec.action == OptimizationAction.PAUSE

    def test_optimize_portfolio_returns_portfolio_optimization(self) -> None:
        optimizer = AdOptimizer()
        campaigns = [
            perf("LOW", ad_spend=100, sales=1000, daily_budget=50),  # ACOS 0.10 → BOOST
            perf("MID", ad_spend=100, sales=400, daily_budget=50),  # ACOS 0.25 → HOLD
            perf("HIGH", ad_spend=700, sales=1000, daily_budget=50),  # ACOS 0.70 → PAUSE
        ]
        result = optimizer.optimize_portfolio(campaigns)
        assert isinstance(result, PortfolioOptimization)
        assert len(result.recommendations) == 3
        actions = {r.campaign_id: r.action for r in result.recommendations}
        assert actions == {
            "LOW": OptimizationAction.BOOST,
            "MID": OptimizationAction.HOLD,
            "HIGH": OptimizationAction.PAUSE,
        }

    def test_budget_reallocation_from_pause_to_boost(self) -> None:
        optimizer = AdOptimizer()
        campaigns = [
            perf("BOOST1", ad_spend=100, sales=1000, daily_budget=50),
            perf("PAUSE1", ad_spend=700, sales=1000, daily_budget=100),
        ]
        result = optimizer.optimize_portfolio(campaigns)
        assert result.budget_reallocation.get("BOOST1", 0) > 0
        assert result.total_projected_spend <= result.total_current_spend

    def test_no_reallocation_when_no_boost(self) -> None:
        optimizer = AdOptimizer()
        campaigns = [
            perf("HOLD", ad_spend=100, sales=400, daily_budget=50),
            perf("PAUSE", ad_spend=700, sales=1000, daily_budget=50),
        ]
        result = optimizer.optimize_portfolio(campaigns)
        assert result.budget_reallocation == {}

    def test_custom_rules(self) -> None:
        rules = OptimizationRules(
            target_acos=0.20,
            boost_threshold=0.10,
            reduce_threshold=0.30,
            pause_threshold=0.50,
        )
        optimizer = AdOptimizer(rules=rules)
        # ACOS 0.35 → PAUSE under custom rules (above 0.50? no, above 0.30 reduce)
        rec = optimizer.recommend(perf(ad_spend=350, sales=1000))
        assert rec.action == OptimizationAction.REDUCE

    def test_reason_includes_acos(self) -> None:
        optimizer = AdOptimizer()
        rec = optimizer.recommend(perf(ad_spend=100, sales=1000))
        assert "ACOS" in rec.reason
