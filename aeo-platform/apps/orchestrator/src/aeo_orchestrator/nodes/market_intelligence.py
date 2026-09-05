"""MV2-03 — market intelligence scan service.

Combines competitor change detection (``competitor_monitor``) with product
re-scoring (``selection_scoring``) to produce a :class:`MarketIntelReport`
for a single SKU.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aeo_shared.competitor_monitor import (
    ListingSnapshot,
    MonitorDiff,
    compute_diff,
)
from aeo_shared.selection_scoring import (
    CompetitorData,
    SelectionInput,
    SelectionResult,
    score_product,
)


@dataclass
class ScanInput:
    """Input for a single-SKU market intelligence scan."""

    sku: str
    platform: str = "amazon"
    marketplace: str = "US"
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None
    category: str | None = None
    brand: str | None = None
    has_title: bool = False
    has_bullets: bool = False
    has_keywords: bool = False
    has_images: bool = False
    previous_competitors: list[ListingSnapshot] = field(default_factory=list)
    current_competitors: list[ListingSnapshot] = field(default_factory=list)
    price_change_threshold: float = 0.05


@dataclass
class MarketIntelReport:
    """Result of a market intelligence scan for one SKU."""

    sku: str
    diff: MonitorDiff
    selection_result: SelectionResult
    suggested_actions: list[str] = field(default_factory=list)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "diff": self.diff.to_dict(),
            "selection": self.selection_result.to_dict(),
            "suggested_actions": self.suggested_actions,
            "scanned_at": self.scanned_at.isoformat(),
        }


class MarketIntelService:
    """Orchestrates competitor diff + selection re-scoring for one SKU."""

    def scan(self, inp: ScanInput) -> MarketIntelReport:
        diff = compute_diff(
            inp.sku,
            inp.previous_competitors,
            inp.current_competitors,
            price_change_threshold=inp.price_change_threshold,
        )

        competitors = [
            CompetitorData(
                asin=s.asin,
                price=s.price,
                rating=s.rating,
                review_count=s.review_count,
            )
            for s in inp.current_competitors
        ]

        selection_result = score_product(
            SelectionInput(
                sku=inp.sku,
                platform=inp.platform,
                marketplace=inp.marketplace,
                price=inp.price,
                rating=inp.rating,
                review_count=inp.review_count,
                category=inp.category,
                brand=inp.brand,
                has_title=inp.has_title,
                has_bullets=inp.has_bullets,
                has_keywords=inp.has_keywords,
                has_images=inp.has_images,
                competitors=competitors,
            )
        )

        actions = _build_actions(diff, selection_result)

        return MarketIntelReport(
            sku=inp.sku,
            diff=diff,
            selection_result=selection_result,
            suggested_actions=actions,
        )


def _build_actions(diff: MonitorDiff, result: SelectionResult) -> list[str]:
    actions: list[str] = []

    if diff.new_listings:
        asins = ", ".join(s.asin for s in diff.new_listings)
        actions.append(f"new competitor(s) detected: {asins}")

    if diff.removed_listings:
        asins = ", ".join(s.asin for s in diff.removed_listings)
        actions.append(f"competitor(s) removed: {asins}")

    price_changes = [c for c in diff.changes if c.field == "price" and c.delta is not None]
    if price_changes:
        increases = [c for c in price_changes if c.delta is not None and c.delta > 0]
        decreases = [c for c in price_changes if c.delta is not None and c.delta < 0]
        if increases:
            actions.append(f"{len(increases)} competitor(s) raised price")
        if decreases:
            actions.append(f"{len(decreases)} competitor(s) lowered price")

    if result.recommendation == "proceed" and diff.has_significant_change:
        actions.append("market shifted — re-review selection before proceeding")

    return actions
