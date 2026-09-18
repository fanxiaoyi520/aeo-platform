"""P7-21: P7-MS3 advanced features acceptance tests.

End-to-end coverage of the P7-MS3 feature set:
  * P7-16/17 auto-pricing
  * P7-18 inventory alerts
  * P7-19 ad optimization
  * P7-20 multi-language listing generation

Each feature is implemented on a sibling branch; we import lazily so
this file still collects on ``main`` before those branches merge.
"""

from __future__ import annotations

from typing import Any

import pytest


def _try_import(module: str, attr: str) -> Any:
    try:
        mod = __import__(module, fromlist=[attr])
        return getattr(mod, attr)
    except (ImportError, AttributeError):
        return None


PricingInputs = _try_import("aeo_shared.pricing", "PricingInputs")
suggest_price = _try_import("aeo_shared.pricing", "suggest_price")
InventorySnapshot = _try_import("aeo_shared.inventory_alerts", "InventorySnapshot")
InventoryAlertService = _try_import(
    "aeo_shared.inventory_alerts", "InventoryAlertService"
)
CampaignPerformance = _try_import(
    "aeo_shared.ad_optimization", "CampaignPerformance"
)
AdOptimizer = _try_import("aeo_shared.ad_optimization", "AdOptimizer")
OptimizationAction = _try_import(
    "aeo_shared.ad_optimization", "OptimizationAction"
)
get_template = _try_import("aeo_shared.i18n_listing", "get_template")
generate_listing = _try_import("aeo_shared.i18n_listing", "generate_listing")


requires_all = pytest.mark.skipif(
    not all(
        [
            PricingInputs,
            suggest_price,
            InventorySnapshot,
            InventoryAlertService,
            CampaignPerformance,
            AdOptimizer,
            OptimizationAction,
            get_template,
            generate_listing,
        ]
    ),
    reason="P7-MS3 feature modules not yet merged",
)


@requires_all
class TestP7MS3Acceptance:
    def test_pricing_suggests_above_roi_floor(self) -> None:
        result = suggest_price(
            PricingInputs(
                current_price=100.0,
                cost=40.0,
                lowest_competitor_price=95.0,
                stock_on_hand=100,
                daily_sales_velocity=10.0,
                target_roi=0.2,
            )
        )
        assert result.suggested_price >= result.roi_floor_price
        assert result.roi_floor_price == 48.0  # 40 * 1.2

    def test_low_stock_triggers_alert_with_restock_qty(self) -> None:
        service = InventoryAlertService()
        snapshot = InventorySnapshot(
            sku="SKU-LOW",
            stock_on_hand=20,
            daily_sales_velocity=5.0,  # 4 days remaining
        )
        alerts = service.evaluate(snapshot)
        assert any(a.kind.value == "low_stock" for a in alerts)
        low = next(a for a in alerts if a.kind.value == "low_stock")
        assert low.suggested_restock_qty > 0

    def test_ad_optimizer_recommends_pause_for_high_acos(self) -> None:
        optimizer = AdOptimizer()
        campaign = CampaignPerformance(
            campaign_id="C1",
            ad_spend=700.0,
            sales=1000.0,  # ACOS 0.70
            current_bid=1.0,
            daily_budget=100.0,
        )
        rec = optimizer.recommend(campaign)
        assert rec.action == OptimizationAction.PAUSE
        assert rec.suggested_bid == 0.0

    def test_i18n_listing_renders_all_four_locales(self) -> None:
        variables = {
            "product_name": "Widget",
            "key_feature": "Fast",
            "benefit_1": "A",
            "benefit_2": "B",
            "benefit_3": "C",
            "use_case": "home",
        }
        for locale in ("en", "de", "ja", "es"):
            template = get_template(locale)
            listing = generate_listing(template, variables)
            assert listing.locale == locale
            assert listing.title
            assert listing.description

    def test_end_to_end_sku_workflow(self) -> None:
        """One SKU flows through pricing → alerts → ads → listing."""
        # Pricing
        price_result = suggest_price(
            PricingInputs(
                current_price=50.0,
                cost=20.0,
                lowest_competitor_price=45.0,
                stock_on_hand=100,
                daily_sales_velocity=10.0,
                target_roi=0.15,
            )
        )
        assert price_result.suggested_price >= 23.0  # 20 * 1.15

        # Inventory
        service = InventoryAlertService()
        snapshot = InventorySnapshot(
            sku="SKU-E2E",
            stock_on_hand=50,
            daily_sales_velocity=10.0,  # 5 days → low stock
        )
        alerts = service.evaluate(snapshot)
        # 5 days of stock → low stock alert
        assert any(a.kind.value == "low_stock" for a in alerts)

        # Ads
        optimizer = AdOptimizer()
        campaign = CampaignPerformance(
            campaign_id="SKU-E2E-AD",
            ad_spend=100.0,
            sales=1000.0,  # ACOS 0.10 → BOOST
            current_bid=1.0,
            daily_budget=50.0,
        )
        rec = optimizer.recommend(campaign)
        assert rec.action == OptimizationAction.BOOST
        assert rec.suggested_bid > 1.0

        # Listing
        template = get_template("en")
        listing = generate_listing(
            template,
            {
                "product_name": "SKU-E2E Widget",
                "key_feature": "Fast",
                "benefit_1": "A",
                "benefit_2": "B",
                "benefit_3": "C",
                "use_case": "home",
            },
        )
        assert "SKU-E2E Widget" in listing.title
