"""P7-18: Inventory alert service.

Evaluates SKU inventory levels against configurable thresholds and
emits alerts when restock or attention is needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertKind(StrEnum):
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCKED = "overstocked"
    VELOCITY_SPIKE = "velocity_spike"
    STAGNANT = "stagnant"


@dataclass(frozen=True)
class InventorySnapshot:
    """Point-in-time inventory reading for one SKU."""

    sku: str
    stock_on_hand: int
    daily_sales_velocity: float
    reorder_point: int = 0
    days_since_last_sale: float = 0.0
    warehouse: str = "default"


@dataclass(frozen=True)
class AlertThresholds:
    """Configurable thresholds for alert evaluation."""

    low_stock_days: float = 7.0
    overstock_days: float = 60.0
    stagnant_days: float = 30.0
    velocity_spike_multiplier: float = 3.0
    baseline_velocity: float = 1.0


@dataclass(frozen=True)
class InventoryAlert:
    """One emitted alert."""

    sku: str
    kind: AlertKind
    severity: AlertSeverity
    message: str
    days_remaining: float
    suggested_restock_qty: int = 0
    warehouse: str = "default"


def days_remaining(
    stock_on_hand: int, daily_sales_velocity: float
) -> float:
    if daily_sales_velocity <= 0:
        return float("inf")
    return stock_on_hand / daily_sales_velocity


def restock_quantity(
    stock_on_hand: int,
    daily_sales_velocity: float,
    target_days: float = 30.0,
) -> int:
    """Suggest a restock quantity to cover ``target_days`` of demand."""
    if daily_sales_velocity <= 0 or target_days <= 0:
        return 0
    needed = int(daily_sales_velocity * target_days)
    delta = needed - stock_on_hand
    return max(0, delta)


@dataclass
class InventoryAlertService:
    """Evaluates snapshots against thresholds and emits alerts."""

    thresholds: AlertThresholds = field(default_factory=AlertThresholds)

    def evaluate(self, snapshot: InventorySnapshot) -> list[InventoryAlert]:
        alerts: list[InventoryAlert] = []
        days = days_remaining(
            snapshot.stock_on_hand, snapshot.daily_sales_velocity
        )

        if snapshot.stock_on_hand <= 0:
            alerts.append(
                InventoryAlert(
                    sku=snapshot.sku,
                    kind=AlertKind.OUT_OF_STOCK,
                    severity=AlertSeverity.CRITICAL,
                    message=f"SKU {snapshot.sku} is out of stock",
                    days_remaining=0.0,
                    suggested_restock_qty=restock_quantity(
                        0, snapshot.daily_sales_velocity
                    ),
                    warehouse=snapshot.warehouse,
                )
            )
            return alerts

        if days <= self.thresholds.low_stock_days:
            alerts.append(
                InventoryAlert(
                    sku=snapshot.sku,
                    kind=AlertKind.LOW_STOCK,
                    severity=AlertSeverity.CRITICAL
                    if days <= self.thresholds.low_stock_days / 2
                    else AlertSeverity.WARNING,
                    message=(
                        f"SKU {snapshot.sku} has {days:.1f} days of stock "
                        f"(threshold {self.thresholds.low_stock_days})"
                    ),
                    days_remaining=days,
                    suggested_restock_qty=restock_quantity(
                        snapshot.stock_on_hand, snapshot.daily_sales_velocity
                    ),
                    warehouse=snapshot.warehouse,
                )
            )
        elif days >= self.thresholds.overstock_days:
            alerts.append(
                InventoryAlert(
                    sku=snapshot.sku,
                    kind=AlertKind.OVERSTOCKED,
                    severity=AlertSeverity.INFO,
                    message=(
                        f"SKU {snapshot.sku} has {days:.1f} days of stock "
                        f"(over {self.thresholds.overstock_days})"
                    ),
                    days_remaining=days,
                    warehouse=snapshot.warehouse,
                )
            )

        if snapshot.daily_sales_velocity >= (
            self.thresholds.baseline_velocity
            * self.thresholds.velocity_spike_multiplier
        ):
            alerts.append(
                InventoryAlert(
                    sku=snapshot.sku,
                    kind=AlertKind.VELOCITY_SPIKE,
                    severity=AlertSeverity.WARNING,
                    message=(
                        f"SKU {snapshot.sku} velocity "
                        f"{snapshot.daily_sales_velocity:.1f} "
                        f">= {self.thresholds.velocity_spike_multiplier}x "
                        f"baseline"
                    ),
                    days_remaining=days,
                    warehouse=snapshot.warehouse,
                )
            )

        if (
            snapshot.days_since_last_sale >= self.thresholds.stagnant_days
            and snapshot.stock_on_hand > 0
        ):
            alerts.append(
                InventoryAlert(
                    sku=snapshot.sku,
                    kind=AlertKind.STAGNANT,
                    severity=AlertSeverity.WARNING,
                    message=(
                        f"SKU {snapshot.sku} no sale for "
                        f"{snapshot.days_since_last_sale:.0f} days"
                    ),
                    days_remaining=days,
                    warehouse=snapshot.warehouse,
                )
            )

        return alerts

    def evaluate_many(
        self, snapshots: list[InventorySnapshot]
    ) -> list[InventoryAlert]:
        alerts: list[InventoryAlert] = []
        for snapshot in snapshots:
            alerts.extend(self.evaluate(snapshot))
        return alerts
