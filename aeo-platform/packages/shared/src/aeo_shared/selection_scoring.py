"""MV2-01 — product selection scoring model.

Scoring dimensions (each 0–100):
- demand: market demand signal (review count, rating)
- competition: competitive intensity (fewer competitors = higher score)
- profitability: price-based margin estimate
- completeness: product data completeness

Total score = weighted average. Recommendation derived from total score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompetitorData:
    """A single competitor listing used for scoring context."""

    asin: str
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None


@dataclass
class SelectionInput:
    """Input data for scoring a product candidate."""

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
    competitors: list[CompetitorData] = field(default_factory=list)


@dataclass
class SelectionResult:
    """Scoring result with dimension breakdown."""

    sku: str
    platform: str
    marketplace: str
    total_score: float
    demand_score: float
    competition_score: float
    profitability_score: float
    completeness_score: float
    competitor_count: int
    recommendation: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "platform": self.platform,
            "marketplace": self.marketplace,
            "total_score": round(self.total_score, 2),
            "demand_score": round(self.demand_score, 2),
            "competition_score": round(self.competition_score, 2),
            "profitability_score": round(self.profitability_score, 2),
            "completeness_score": round(self.completeness_score, 2),
            "competitor_count": self.competitor_count,
            "recommendation": self.recommendation,
            "detail": self.detail,
        }


_DEMAND_WEIGHT = 0.30
_COMPETITION_WEIGHT = 0.25
_PROFITABILITY_WEIGHT = 0.25
_COMPLETENESS_WEIGHT = 0.20


def _score_demand(review_count: int | None, rating: float | None) -> float:
    if review_count is None and rating is None:
        return 50.0
    score = 0.0
    if review_count is not None:
        review_score = min(review_count / 500, 1.0) * 60
        score += review_score
    else:
        score += 30
    if rating is not None:
        rating_score = min(max(rating / 5.0, 0), 1.0) * 40
        score += rating_score
    else:
        score += 20
    return min(score, 100.0)


def _score_competition(competitors: list[CompetitorData]) -> float:
    count = len(competitors)
    if count == 0:
        return 80.0
    if count <= 3:
        return 70.0
    if count <= 10:
        return 50.0
    if count <= 30:
        return 30.0
    return 10.0


def _score_profitability(price: float | None, competitors: list[CompetitorData]) -> float:
    if price is None or price <= 0:
        return 30.0
    competitor_prices = [c.price for c in competitors if c.price is not None and c.price > 0]
    if not competitor_prices:
        if price >= 20:
            return 70.0
        return 50.0
    avg_competitor = sum(competitor_prices) / len(competitor_prices)
    if price <= avg_competitor * 0.8:
        return 40.0
    if price <= avg_competitor * 1.2:
        return 80.0
    if price <= avg_competitor * 1.5:
        return 60.0
    return 30.0


def _score_completeness(
    has_title: bool,
    has_bullets: bool,
    has_keywords: bool,
    has_images: bool,
) -> float:
    fields = [has_title, has_bullets, has_keywords, has_images]
    return sum(25.0 for f in fields if f)


def _recommendation(total_score: float) -> str:
    if total_score >= 75:
        return "proceed"
    if total_score >= 50:
        return "review"
    return "skip"


def score_product(input_data: SelectionInput) -> SelectionResult:
    demand = _score_demand(input_data.review_count, input_data.rating)
    competition = _score_competition(input_data.competitors)
    profitability = _score_profitability(input_data.price, input_data.competitors)
    completeness = _score_completeness(
        input_data.has_title,
        input_data.has_bullets,
        input_data.has_keywords,
        input_data.has_images,
    )
    total = (
        demand * _DEMAND_WEIGHT
        + competition * _COMPETITION_WEIGHT
        + profitability * _PROFITABILITY_WEIGHT
        + completeness * _COMPLETENESS_WEIGHT
    )
    return SelectionResult(
        sku=input_data.sku,
        platform=input_data.platform,
        marketplace=input_data.marketplace,
        total_score=total,
        demand_score=demand,
        competition_score=competition,
        profitability_score=profitability,
        completeness_score=completeness,
        competitor_count=len(input_data.competitors),
        recommendation=_recommendation(total),
        detail={
            "weights": {
                "demand": _DEMAND_WEIGHT,
                "competition": _COMPETITION_WEIGHT,
                "profitability": _PROFITABILITY_WEIGHT,
                "completeness": _COMPLETENESS_WEIGHT,
            },
        },
    )
