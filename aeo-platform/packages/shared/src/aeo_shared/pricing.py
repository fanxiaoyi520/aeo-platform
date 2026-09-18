"""P7-16/17: Auto-pricing algorithm.

Suggests a sale price by combining three signals:
  * **competition** — position relative to the lowest competitor
  * **inventory** — days of stock remaining
  * **roi** — minimum acceptable margin over cost

The three signals produce independent candidate prices; the final
suggestion is their weighted average, clamped to the ROI floor and
the platform's min/max bounds.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PricingInputs:
    """Inputs required to compute a pricing suggestion."""

    current_price: float
    cost: float
    lowest_competitor_price: float
    stock_on_hand: int
    daily_sales_velocity: float
    target_roi: float = 0.2
    platform_min_price: float = 0.01
    platform_max_price: float = 10_000.0


@dataclass(frozen=True)
class PricingSuggestion:
    """Output of the pricing algorithm."""

    suggested_price: float
    competition_price: float
    inventory_price: float
    roi_floor_price: float
    reason: str


def days_of_stock_remaining(
    stock_on_hand: int, daily_sales_velocity: float
) -> float:
    if daily_sales_velocity <= 0:
        return float("inf")
    return stock_on_hand / daily_sales_velocity


def competition_candidate(
    current_price: float, lowest_competitor_price: float
) -> float:
    """Undercut the lowest competitor by a small margin when we are
    already close; otherwise stay put."""
    if lowest_competitor_price <= 0:
        return current_price
    delta = lowest_competitor_price - current_price
    if delta > 0:
        # We are cheaper; keep the advantage but capture up to half the gap.
        return current_price + delta / 2
    # We are more expensive; undercut by 1% to win the buy-box.
    return lowest_competitor_price * 0.99


def inventory_candidate(
    current_price: float, days_remaining: float
) -> float:
    """Adjust price based on stock health."""
    if days_remaining == float("inf"):
        return current_price
    if days_remaining < 7:
        # Low stock — raise price 5% to slow depletion.
        return current_price * 1.05
    if days_remaining < 21:
        # Healthy — hold.
        return current_price
    # Overstocked — drop price 5% to accelerate turnover.
    return current_price * 0.95


def roi_floor_price(cost: float, target_roi: float) -> float:
    """Minimum price that satisfies the target ROI."""
    if target_roi < 0:
        return cost
    return cost * (1 + target_roi)


def suggest_price(inputs: PricingInputs) -> PricingSuggestion:
    """Compute a weighted-average pricing suggestion."""
    if inputs.cost <= 0:
        msg = "cost must be positive"
        raise ValueError(msg)
    if inputs.current_price <= 0:
        msg = "current_price must be positive"
        raise ValueError(msg)

    days_remaining = days_of_stock_remaining(
        inputs.stock_on_hand, inputs.daily_sales_velocity
    )
    competition = competition_candidate(
        inputs.current_price, inputs.lowest_competitor_price
    )
    inventory = inventory_candidate(inputs.current_price, days_remaining)
    roi_floor = roi_floor_price(inputs.cost, inputs.target_roi)

    # Weights: competition matters most, then inventory, then ROI floor
    # acts as a hard constraint rather than a weighted contributor.
    weighted = (
        0.5 * competition
        + 0.3 * inventory
        + 0.2 * max(inputs.current_price, roi_floor)
    )
    clamped = max(
        inputs.platform_min_price,
        min(inputs.platform_max_price, max(weighted, roi_floor)),
    )
    reason = _build_reason(days_remaining, competition, inventory, roi_floor)
    return PricingSuggestion(
        suggested_price=_round_price(clamped),
        competition_price=_round_price(competition),
        inventory_price=_round_price(inventory),
        roi_floor_price=_round_price(roi_floor),
        reason=reason,
    )


def _round_price(price: float) -> float:
    return round(price, 2)


def _build_reason(
    days_remaining: float,
    competition: float,
    inventory: float,
    roi_floor: float,
) -> str:
    parts: list[str] = []
    if days_remaining != float("inf") and days_remaining < 7:
        parts.append("low stock (+5%)")
    elif days_remaining != float("inf") and days_remaining > 21:
        parts.append("overstocked (-5%)")
    else:
        parts.append("stock healthy")
    if competition < inventory:
        parts.append("price competition")
    if roi_floor > competition:
        parts.append("ROI floor binding")
    return "; ".join(parts)
