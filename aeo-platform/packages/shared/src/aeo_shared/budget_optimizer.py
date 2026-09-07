"""MV3-03: Budget allocation + ROI projection engine.

Performance-weighted budget allocation based on ACoS/ROI analysis.
Linear extrapolation for ROI projection and what-if simulation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class BudgetAllocation(BaseModel):
    """Budget allocation recommendation for a single campaign."""

    campaign_id: str
    current_budget: Decimal
    suggested_budget: Decimal
    change_percent: float
    reason: str = ""


class ROIProjection(BaseModel):
    """ROI projection for a campaign over a time period."""

    campaign_id: str
    projection_days: int
    estimated_spend: Decimal
    estimated_gmv: Decimal
    estimated_roi: float
    confidence: float


class WhatIfResult(BaseModel):
    """What-if simulation result for budget change."""

    campaign_id: str
    budget_change_percent: float
    current_spend: Decimal
    projected_spend: Decimal
    projected_gmv_change_percent: float
    projected_acos_change: float


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _calculate_acos(spend: Decimal, gmv: Decimal) -> float:
    if gmv <= 0:
        return 100.0
    return float(spend / gmv * 100)


def _calculate_roi(spend: Decimal, gmv: Decimal) -> float:
    if spend <= 0:
        return 0.0
    return float(gmv / spend)


class BudgetOptimizer:
    """Budget allocation and ROI projection engine."""

    def allocate_budget(
        self,
        campaigns: list[dict[str, Any]],
        snapshots: list[dict[str, Any]],
    ) -> list[BudgetAllocation]:
        """Allocate budget based on campaign performance (lower ACoS = more budget)."""
        by_campaign: dict[str, list[dict[str, Any]]] = {}
        for snap in snapshots:
            cid = str(snap.get("campaign_id", ""))
            by_campaign.setdefault(cid, []).append(snap)

        campaign_perf: list[tuple[dict[str, Any], Decimal, Decimal, float]] = []
        for camp in campaigns:
            if camp.get("status") != "enabled":
                continue
            cid = str(camp.get("campaign_id", ""))
            camp_snaps = by_campaign.get(cid, [])
            total_spend = sum(_to_decimal(s.get("spend")) for s in camp_snaps)
            total_gmv = sum(_to_decimal(s.get("attributed_gmv")) for s in camp_snaps)
            acos = _calculate_acos(total_spend, total_gmv)
            campaign_perf.append((camp, total_spend, total_gmv, acos))

        if not campaign_perf:
            return []

        best_acos = min(p[3] for p in campaign_perf)
        allocations = []
        for camp, spend, gmv, acos in campaign_perf:
            cid = str(camp.get("campaign_id", ""))
            current = _to_decimal(camp.get("daily_budget"))

            acos_gap = best_acos - acos
            if acos_gap < -5:
                change_pct = -10.0
                reason = f"ACoS {acos:.1f}% above best, reduce budget"
            elif acos_gap < 0:
                change_pct = 15.0 + min(20.0, abs(acos_gap) * 2)
                reason = f"ACoS {acos:.1f}% competitive, increase budget"
            else:
                change_pct = 25.0 + min(25.0, abs(acos_gap) * 3)
                reason = f"Best ACoS {acos:.1f}%, scale up"

            suggested = current * Decimal(str(1 + change_pct / 100))
            allocations.append(
                BudgetAllocation(
                    campaign_id=cid,
                    current_budget=current,
                    suggested_budget=suggested.quantize(Decimal("0.01")),
                    change_percent=round(change_pct, 1),
                    reason=reason,
                )
            )

        return allocations

    def project_roi(
        self,
        campaign_id: str,
        snapshots: list[dict[str, Any]],
        days: int = 7,
    ) -> ROIProjection:
        """Project ROI for a campaign over the specified time period."""
        camp_snaps = [
            s for s in snapshots if str(s.get("campaign_id", "")) == campaign_id
        ]
        if not camp_snaps:
            return ROIProjection(
                campaign_id=campaign_id,
                projection_days=days,
                estimated_spend=Decimal("0"),
                estimated_gmv=Decimal("0"),
                estimated_roi=0.0,
                confidence=0.0,
            )

        total_spend = sum(_to_decimal(s.get("spend")) for s in camp_snaps)
        total_gmv = sum(_to_decimal(s.get("attributed_gmv")) for s in camp_snaps)
        num_days = len(camp_snaps)

        avg_daily_spend = total_spend / num_days
        avg_daily_gmv = total_gmv / num_days

        projected_spend = (avg_daily_spend * days).quantize(Decimal("0.01"))
        projected_gmv = (avg_daily_gmv * days).quantize(Decimal("0.01"))
        roi = _calculate_roi(projected_spend, projected_gmv)

        confidence = min(0.9, 0.5 + num_days * 0.1)

        return ROIProjection(
            campaign_id=campaign_id,
            projection_days=days,
            estimated_spend=projected_spend,
            estimated_gmv=projected_gmv,
            estimated_roi=round(roi, 2),
            confidence=round(confidence, 2),
        )

    def simulate_what_if(
        self,
        campaign_id: str,
        snapshots: list[dict[str, Any]],
        budget_change_percent: float,
    ) -> WhatIfResult:
        """Simulate the impact of a budget change on a campaign."""
        camp_snaps = [
            s for s in snapshots if str(s.get("campaign_id", "")) == campaign_id
        ]
        if not camp_snaps:
            return WhatIfResult(
                campaign_id=campaign_id,
                budget_change_percent=budget_change_percent,
                current_spend=Decimal("0"),
                projected_spend=Decimal("0"),
                projected_gmv_change_percent=0.0,
                projected_acos_change=0.0,
            )

        current_spend = sum(_to_decimal(s.get("spend")) for s in camp_snaps)
        current_gmv = sum(_to_decimal(s.get("attributed_gmv")) for s in camp_snaps)
        current_acos = _calculate_acos(current_spend, current_gmv)

        multiplier = 1 + budget_change_percent / 100
        projected_spend = (current_spend * Decimal(str(multiplier))).quantize(Decimal("0.01"))

        elasticity = 0.6
        gmv_multiplier = 1 + (budget_change_percent / 100) * elasticity
        projected_gmv = (current_gmv * Decimal(str(gmv_multiplier))).quantize(Decimal("0.01"))

        gmv_change_pct = (float(projected_gmv / current_gmv) - 1) * 100 if current_gmv > 0 else 0.0
        projected_acos = _calculate_acos(projected_spend, projected_gmv)
        acos_change = projected_acos - current_acos

        return WhatIfResult(
            campaign_id=campaign_id,
            budget_change_percent=budget_change_percent,
            current_spend=current_spend,
            projected_spend=projected_spend,
            projected_gmv_change_percent=round(gmv_change_pct, 1),
            projected_acos_change=round(acos_change, 2),
        )
