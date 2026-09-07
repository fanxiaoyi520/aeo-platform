"""MV3-07: Ads-inventory linkage strategy engine.

Cross-references ads campaign performance with inventory health
to produce stock-aware budget adjustment recommendations.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

CRITICAL_THRESHOLD = 10
LOW_THRESHOLD = 25
OVERSTOCK_THRESHOLD = 100


class StockStatus(StrEnum):
    CRITICAL = "critical"
    LOW = "low"
    HEALTHY = "healthy"
    OVERSTOCK = "overstock"


class LinkageRecommendation(BaseModel):
    campaign_id: str
    sku: str
    stock_status: StockStatus
    current_budget: Decimal
    suggested_budget: Decimal
    budget_change_percent: float
    reason: str = ""
    urgency: str = "low"


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _classify_stock(quantity: int) -> StockStatus:
    if quantity < CRITICAL_THRESHOLD:
        return StockStatus.CRITICAL
    if quantity < LOW_THRESHOLD:
        return StockStatus.LOW
    if quantity >= OVERSTOCK_THRESHOLD:
        return StockStatus.OVERSTOCK
    return StockStatus.HEALTHY


class AdsInventoryLinkage:
    """Cross-reference ads performance with inventory to produce coordinated recs."""

    def analyze(
        self,
        campaigns: list[dict[str, Any]],
        snapshots: list[dict[str, Any]],
        inventory: list[dict[str, Any]],
    ) -> list[LinkageRecommendation]:
        inv_by_sku: dict[str, int] = {}
        for item in inventory:
            sku = str(item.get("sku", ""))
            inv_by_sku[sku] = int(item.get("available_quantity", 0))

        spend_by_campaign: dict[str, Decimal] = {}
        for snap in snapshots:
            cid = str(snap.get("campaign_id", ""))
            spend_by_campaign[cid] = spend_by_campaign.get(cid, Decimal("0")) + _to_decimal(
                snap.get("spend")
            )

        recommendations: list[LinkageRecommendation] = []
        for camp in campaigns:
            if camp.get("status") != "enabled":
                continue

            cid = str(camp.get("campaign_id", ""))
            sku = str(camp.get("sku", ""))
            current_budget = _to_decimal(camp.get("daily_budget"))

            stock_qty = inv_by_sku.get(sku, 0) if inventory else 0
            stock_status = _classify_stock(stock_qty) if inventory else StockStatus.HEALTHY

            change_pct, reason, urgency = self._compute_adjustment(
                stock_status, current_budget, spend_by_campaign.get(cid, Decimal("0"))
            )

            suggested = (current_budget * Decimal(str(1 + change_pct / 100))).quantize(
                Decimal("0.01")
            )
            if suggested < 0:
                suggested = Decimal("0")

            recommendations.append(
                LinkageRecommendation(
                    campaign_id=cid,
                    sku=sku,
                    stock_status=stock_status,
                    current_budget=current_budget,
                    suggested_budget=suggested,
                    budget_change_percent=round(change_pct, 1),
                    reason=reason,
                    urgency=urgency,
                )
            )

        return recommendations

    def _compute_adjustment(
        self,
        stock_status: StockStatus,
        current_budget: Decimal,
        total_spend: Decimal,
    ) -> tuple[float, str, str]:
        if stock_status == StockStatus.CRITICAL:
            return (
                -50.0,
                "Critical stock — halve ad spend to conserve capital",
                "high",
            )
        if stock_status == StockStatus.LOW:
            return (
                -25.0,
                "Low stock — reduce ad spend, prioritize restock",
                "high",
            )
        if stock_status == StockStatus.OVERSTOCK:
            return (
                20.0,
                "Overstocked — increase ad spend to accelerate turnover",
                "medium",
            )
        return (
            5.0,
            "Healthy stock — slight budget increase for sustained growth",
            "low",
        )
