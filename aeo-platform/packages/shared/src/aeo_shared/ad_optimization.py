"""P7-19: Ad optimization algorithm.

Suggests bid and budget adjustments based on campaign ACOS relative
to a target threshold.

Actions:
  * ``BOOST`` — campaign ACOS well below target → raise bid to capture
    more impressions
  * ``HOLD`` — campaign within tolerance band
  * ``REDUCE`` — campaign above target → lower bid to stop bleeding
  * ``PAUSE`` — campaign far above target → pause to cut losses

Budget reallocation moves freed budget from paused/reduced campaigns
into the best-performing boosted campaigns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class OptimizationAction(StrEnum):
    BOOST = "boost"
    HOLD = "hold"
    REDUCE = "reduce"
    PAUSE = "pause"


@dataclass(frozen=True)
class CampaignPerformance:
    """One campaign's performance snapshot."""

    campaign_id: str
    ad_spend: float
    sales: float
    current_bid: float
    daily_budget: float
    impressions: int = 0
    clicks: int = 0

    @property
    def acos(self) -> float:
        if self.sales <= 0:
            return float("inf")
        return self.ad_spend / self.sales

    @property
    def roas(self) -> float:
        if self.ad_spend <= 0:
            return 0.0
        return self.sales / self.ad_spend


@dataclass(frozen=True)
class OptimizationRules:
    """Tunable optimization parameters."""

    target_acos: float = 0.25
    boost_threshold: float = 0.15  # ACOS ≤ this → boost
    reduce_threshold: float = 0.35  # ACOS ≥ this → reduce
    pause_threshold: float = 0.60  # ACOS ≥ this → pause
    max_bid_increase_pct: float = 0.20
    max_bid_decrease_pct: float = 0.20
    min_bid: float = 0.05


@dataclass(frozen=True)
class CampaignRecommendation:
    """One campaign's optimization recommendation."""

    campaign_id: str
    action: OptimizationAction
    current_acos: float
    current_bid: float
    suggested_bid: float
    bid_delta_pct: float
    reason: str


@dataclass(frozen=True)
class PortfolioOptimization:
    """Full-portfolio optimization result."""

    recommendations: list[CampaignRecommendation]
    total_current_spend: float
    total_projected_spend: float
    budget_reallocation: dict[str, float] = field(default_factory=dict)


def classify_campaign(
    acos: float, rules: OptimizationRules
) -> OptimizationAction:
    if acos >= rules.pause_threshold:
        return OptimizationAction.PAUSE
    if acos >= rules.reduce_threshold:
        return OptimizationAction.REDUCE
    if acos <= rules.boost_threshold:
        return OptimizationAction.BOOST
    return OptimizationAction.HOLD


def compute_bid_adjustment(
    current_bid: float,
    action: OptimizationAction,
    current_acos: float,
    rules: OptimizationRules,
) -> tuple[float, float]:
    """Return (suggested_bid, delta_pct)."""
    if action == OptimizationAction.BOOST:
        # Scale boost by how far below boost threshold we are.
        headroom = rules.boost_threshold - min(current_acos, rules.boost_threshold)
        scale = min(1.0, headroom / max(rules.boost_threshold, 1e-6))
        delta_pct = rules.max_bid_increase_pct * scale
        suggested = current_bid * (1 + delta_pct)
    elif action == OptimizationAction.REDUCE:
        overshoot = current_acos - rules.reduce_threshold
        scale = min(
            1.0,
            overshoot / max(rules.pause_threshold - rules.reduce_threshold, 1e-6),
        )
        delta_pct = -rules.max_bid_decrease_pct * scale
        suggested = current_bid * (1 + delta_pct)
    elif action == OptimizationAction.PAUSE:
        delta_pct = -1.0
        suggested = 0.0
    else:  # HOLD
        delta_pct = 0.0
        suggested = current_bid
    suggested = max(rules.min_bid, suggested) if action != OptimizationAction.PAUSE else 0.0
    return suggested, delta_pct


@dataclass
class AdOptimizer:
    """Applies rules to a portfolio of campaigns."""

    rules: OptimizationRules = field(default_factory=OptimizationRules)

    def recommend(self, campaign: CampaignPerformance) -> CampaignRecommendation:
        acos = campaign.acos
        action = classify_campaign(acos, self.rules)
        suggested_bid, delta_pct = compute_bid_adjustment(
            campaign.current_bid, action, acos, self.rules
        )
        reason = self._reason(action, acos)
        return CampaignRecommendation(
            campaign_id=campaign.campaign_id,
            action=action,
            current_acos=round(acos, 4) if acos != float("inf") else float("inf"),
            current_bid=campaign.current_bid,
            suggested_bid=round(suggested_bid, 2),
            bid_delta_pct=round(delta_pct, 4),
            reason=reason,
        )

    def optimize_portfolio(
        self, campaigns: list[CampaignPerformance]
    ) -> PortfolioOptimization:
        recommendations = [self.recommend(c) for c in campaigns]
        total_current = sum(c.daily_budget for c in campaigns)
        freed = 0.0
        boosted_budget_need = 0.0
        for campaign, rec in zip(campaigns, recommendations, strict=True):
            if rec.action == OptimizationAction.PAUSE:
                freed += campaign.daily_budget
            elif rec.action == OptimizationAction.REDUCE:
                freed += campaign.daily_budget * abs(rec.bid_delta_pct)
            elif rec.action == OptimizationAction.BOOST:
                boosted_budget_need += campaign.daily_budget * rec.bid_delta_pct
        reallocation: dict[str, float] = {}
        if boosted_budget_need > 0 and freed > 0:
            boost_ids = [
                r.campaign_id
                for r in recommendations
                if r.action == OptimizationAction.BOOST
            ]
            share = freed / max(len(boost_ids), 1)
            for cid in boost_ids:
                reallocation[cid] = round(share, 2)
        projected = total_current - freed + sum(reallocation.values())
        return PortfolioOptimization(
            recommendations=recommendations,
            total_current_spend=round(total_current, 2),
            total_projected_spend=round(projected, 2),
            budget_reallocation=reallocation,
        )

    @staticmethod
    def _reason(action: OptimizationAction, acos: float) -> str:
        acos_str = "∞" if acos == float("inf") else f"{acos:.2%}"
        return {
            OptimizationAction.BOOST: f"ACOS {acos_str} ≤ target — raise bid",
            OptimizationAction.HOLD: f"ACOS {acos_str} within tolerance",
            OptimizationAction.REDUCE: f"ACOS {acos_str} above target — lower bid",
            OptimizationAction.PAUSE: f"ACOS {acos_str} far above target — pause",
        }[action]
