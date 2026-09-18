"""P7-18: Tests for inventory alert service."""

from __future__ import annotations

from aeo_shared.inventory_alerts import (
    AlertKind,
    AlertSeverity,
    AlertThresholds,
    InventoryAlert,
    InventoryAlertService,
    InventorySnapshot,
    days_remaining,
    restock_quantity,
)


class TestDaysRemaining:
    def test_zero_velocity_returns_infinity(self) -> None:
        assert days_remaining(100, 0) == float("inf")

    def test_normal_calculation(self) -> None:
        assert days_remaining(100, 10) == 10.0


class TestRestockQuantity:
    def test_suggests_quantity_to_cover_target_days(self) -> None:
        # 10/day * 30 days = 300 needed; have 50 → suggest 250
        assert restock_quantity(50, 10.0, target_days=30) == 250

    def test_no_restock_when_over_target(self) -> None:
        assert restock_quantity(500, 10.0, target_days=30) == 0

    def test_zero_velocity_returns_zero(self) -> None:
        assert restock_quantity(100, 0.0) == 0


class TestInventoryAlertService:
    def test_out_of_stock_emits_critical(self) -> None:
        service = InventoryAlertService()
        snapshot = InventorySnapshot(sku="SKU-1", stock_on_hand=0, daily_sales_velocity=5.0)
        alerts = service.evaluate(snapshot)
        assert len(alerts) == 1
        assert alerts[0].kind == AlertKind.OUT_OF_STOCK
        assert alerts[0].severity == AlertSeverity.CRITICAL
        assert alerts[0].suggested_restock_qty == 150  # 5 * 30

    def test_low_stock_emits_warning(self) -> None:
        service = InventoryAlertService()
        # 5 days of stock (below 7-day threshold)
        snapshot = InventorySnapshot(sku="SKU-2", stock_on_hand=50, daily_sales_velocity=10.0)
        alerts = service.evaluate(snapshot)
        assert any(a.kind == AlertKind.LOW_STOCK for a in alerts)
        low = next(a for a in alerts if a.kind == AlertKind.LOW_STOCK)
        assert low.severity == AlertSeverity.WARNING
        assert low.suggested_restock_qty > 0

    def test_very_low_stock_emits_critical(self) -> None:
        service = InventoryAlertService()
        # 3 days of stock (below half of 7-day threshold → critical)
        snapshot = InventorySnapshot(sku="SKU-3", stock_on_hand=15, daily_sales_velocity=5.0)
        alerts = service.evaluate(snapshot)
        low = next(a for a in alerts if a.kind == AlertKind.LOW_STOCK)
        assert low.severity == AlertSeverity.CRITICAL

    def test_overstocked_emits_info(self) -> None:
        service = InventoryAlertService()
        # 100 days of stock (> 60-day threshold)
        snapshot = InventorySnapshot(sku="SKU-4", stock_on_hand=1000, daily_sales_velocity=10.0)
        alerts = service.evaluate(snapshot)
        assert any(a.kind == AlertKind.OVERSTOCKED for a in alerts)
        over = next(a for a in alerts if a.kind == AlertKind.OVERSTOCKED)
        assert over.severity == AlertSeverity.INFO

    def test_velocity_spike_detected(self) -> None:
        service = InventoryAlertService()
        # Baseline 1, spike multiplier 3 → threshold 3; velocity 10 triggers
        snapshot = InventorySnapshot(
            sku="SKU-5", stock_on_hand=500, daily_sales_velocity=10.0
        )
        alerts = service.evaluate(snapshot)
        assert any(a.kind == AlertKind.VELOCITY_SPIKE for a in alerts)

    def test_stagnant_stock_detected(self) -> None:
        service = InventoryAlertService()
        snapshot = InventorySnapshot(
            sku="SKU-6",
            stock_on_hand=100,
            daily_sales_velocity=0.1,
            days_since_last_sale=40.0,
        )
        alerts = service.evaluate(snapshot)
        assert any(a.kind == AlertKind.STAGNANT for a in alerts)

    def test_healthy_stock_no_alerts(self) -> None:
        service = InventoryAlertService()
        # 20 days of stock, normal velocity (within baseline), recent sale
        snapshot = InventorySnapshot(
            sku="SKU-7",
            stock_on_hand=40,
            daily_sales_velocity=2.0,
            days_since_last_sale=1.0,
        )
        alerts = service.evaluate(snapshot)
        assert alerts == []

    def test_evaluate_many_aggregates(self) -> None:
        service = InventoryAlertService()
        snapshots = [
            InventorySnapshot(
                sku="GOOD", stock_on_hand=40, daily_sales_velocity=2.0
            ),
            InventorySnapshot(
                sku="EMPTY", stock_on_hand=0, daily_sales_velocity=5.0
            ),
            InventorySnapshot(
                sku="LOW", stock_on_hand=10, daily_sales_velocity=2.0
            ),
        ]
        alerts = service.evaluate_many(snapshots)
        skus_with_alerts = {a.sku for a in alerts}
        assert "GOOD" not in skus_with_alerts
        assert "EMPTY" in skus_with_alerts
        assert "LOW" in skus_with_alerts

    def test_custom_thresholds(self) -> None:
        thresholds = AlertThresholds(low_stock_days=14.0, overstock_days=30.0)
        service = InventoryAlertService(thresholds=thresholds)
        # 10 days of stock: below 14-day threshold → low stock
        snapshot = InventorySnapshot(sku="SKU-8", stock_on_hand=100, daily_sales_velocity=10.0)
        alerts = service.evaluate(snapshot)
        assert any(a.kind == AlertKind.LOW_STOCK for a in alerts)

    def test_alert_is_dataclass(self) -> None:
        service = InventoryAlertService()
        snapshot = InventorySnapshot(sku="SKU-9", stock_on_hand=0, daily_sales_velocity=1.0)
        alerts = service.evaluate(snapshot)
        assert isinstance(alerts[0], InventoryAlert)
