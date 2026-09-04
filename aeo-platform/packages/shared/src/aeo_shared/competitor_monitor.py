"""Competitor change detection — pure logic, no framework dependencies.

Compares a *previous* snapshot of competitor listings against a *current*
snapshot and produces a :class:`MonitorDiff` describing price / rating /
review-count deltas, new entrants, and removed listings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ListingSnapshot:
    """Point-in-time view of one competitor listing."""

    asin: str
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None


@dataclass
class ListingChange:
    """A single field-level change for one competitor listing."""

    asin: str
    field: str  # "price" | "rating" | "review_count"
    old_value: float | int | None
    new_value: float | int | None
    delta: float | int | None = None


@dataclass
class MonitorDiff:
    """Result of comparing two competitor snapshots for one SKU."""

    sku: str
    changes: list[ListingChange] = field(default_factory=list)
    new_listings: list[ListingSnapshot] = field(default_factory=list)
    removed_listings: list[ListingSnapshot] = field(default_factory=list)
    has_significant_change: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "changes": [
                {
                    "asin": c.asin,
                    "field": c.field,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "delta": c.delta,
                }
                for c in self.changes
            ],
            "new_listings": [
                {
                    "asin": s.asin,
                    "price": s.price,
                    "rating": s.rating,
                    "review_count": s.review_count,
                }
                for s in self.new_listings
            ],
            "removed_listings": [
                {
                    "asin": s.asin,
                    "price": s.price,
                    "rating": s.rating,
                    "review_count": s.review_count,
                }
                for s in self.removed_listings
            ],
            "has_significant_change": self.has_significant_change,
        }


def compute_diff(
    sku: str,
    previous: list[ListingSnapshot],
    current: list[ListingSnapshot],
    *,
    price_change_threshold: float = 0.05,
) -> MonitorDiff:
    """Compare *previous* and *current* snapshots and return a :class:`MonitorDiff`.

    A change is *significant* when any price delta exceeds
    *price_change_threshold* (relative, e.g. 0.05 = 5 %) or when listings
    appear / disappear.
    """
    prev_map: dict[str, ListingSnapshot] = {s.asin: s for s in previous}
    curr_map: dict[str, ListingSnapshot] = {s.asin: s for s in current}

    changes: list[ListingChange] = []
    significant = False

    for asin in prev_map.keys() & curr_map.keys():
        old = prev_map[asin]
        new = curr_map[asin]
        changes.extend(_compare_listing(old, new, price_change_threshold))
        if _price_is_significant(old.price, new.price, price_change_threshold):
            significant = True

    new_listings = [curr_map[a] for a in curr_map if a not in prev_map]
    removed_listings = [prev_map[a] for a in prev_map if a not in curr_map]

    if new_listings or removed_listings:
        significant = True

    return MonitorDiff(
        sku=sku,
        changes=changes,
        new_listings=new_listings,
        removed_listings=removed_listings,
        has_significant_change=significant,
    )


def _compare_listing(
    old: ListingSnapshot,
    new: ListingSnapshot,
    threshold: float,
) -> list[ListingChange]:
    result: list[ListingChange] = []
    if old.price != new.price:
        delta = _numeric_delta(old.price, new.price)
        result.append(ListingChange(old.asin, "price", old.price, new.price, delta))
    if old.rating != new.rating:
        delta = _numeric_delta(old.rating, new.rating)
        result.append(ListingChange(old.asin, "rating", old.rating, new.rating, delta))
    if old.review_count != new.review_count:
        delta = _numeric_delta(old.review_count, new.review_count)
        result.append(
            ListingChange(old.asin, "review_count", old.review_count, new.review_count, delta)
        )
    return result


def _price_is_significant(
    old_price: float | None,
    new_price: float | None,
    threshold: float,
) -> bool:
    if old_price is None or new_price is None:
        return old_price != new_price
    if old_price == 0:
        return new_price != 0
    return abs(new_price - old_price) / old_price > threshold


def _numeric_delta(
    old: float | int | None,
    new: float | int | None,
) -> float | int | None:
    if old is None or new is None:
        return None
    return new - old
