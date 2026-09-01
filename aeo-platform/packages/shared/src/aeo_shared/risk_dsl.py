"""MV1-04 — L0/L1/L2 risk rule DSL (MV-M02 foundation)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from aeo_shared.agent_registry import RiskLevel


class RiskAction(StrEnum):
    """Normalized write/read actions for risk evaluation."""

    RESEARCH_READ = "research.read"
    LISTING_GENERATE = "listing.generate"
    LISTING_PUBLISH = "listing.publish"
    LISTING_UPDATE = "listing.update"
    PRICE_UPDATE = "price.update"
    ADS_BID_CHANGE = "ads.bid_change"
    ADS_BUDGET_CHANGE = "ads.budget_change"
    ORDER_REFUND = "order.refund"
    ACCOUNT_OPEN = "account.open"


class RiskEffect(StrEnum):
    ALLOW = "allow"
    REQUIRE_HITL = "require_hitl"
    DENY = "deny"


RiskOperator = Literal["eq", "gt", "gte", "lt", "lte", "in"]


class RiskCondition(BaseModel):
    field: str
    operator: RiskOperator = "eq"
    value: Any


class RiskRule(BaseModel):
    rule_id: str
    action: RiskAction
    risk_level: RiskLevel
    effect: RiskEffect
    description: str = ""
    conditions: list[RiskCondition] = Field(default_factory=list)
    priority: int = 100


class RiskRuleSet(BaseModel):
    version: str = "1.0"
    rules: list[RiskRule] = Field(default_factory=list)

    def sorted_rules(self) -> list[RiskRule]:
        return sorted(self.rules, key=lambda rule: rule.priority)


class RiskDecision(BaseModel):
    allowed: bool
    effect: RiskEffect
    risk_level: RiskLevel
    rule_id: str
    message: str = ""


def _match_conditions(conditions: list[RiskCondition], context: dict[str, Any]) -> bool:
    if not conditions:
        return True
    for condition in conditions:
        actual = context.get(condition.field)
        if condition.operator == "eq" and actual != condition.value:
            return False
        if condition.operator == "gt" and not (actual is not None and actual > condition.value):
            return False
        if condition.operator == "gte" and not (actual is not None and actual >= condition.value):
            return False
        if condition.operator == "lt" and not (actual is not None and actual < condition.value):
            return False
        if condition.operator == "lte" and not (actual is not None and actual <= condition.value):
            return False
        if condition.operator == "in" and actual not in condition.value:
            return False
    return True


def evaluate_action(
    action: RiskAction | str,
    context: dict[str, Any] | None,
    rule_set: RiskRuleSet,
) -> RiskDecision:
    ctx = context or {}
    action_value = RiskAction(action) if not isinstance(action, RiskAction) else action

    for rule in rule_set.sorted_rules():
        if rule.action != action_value:
            continue
        if not _match_conditions(rule.conditions, ctx):
            continue
        allowed = rule.effect == RiskEffect.ALLOW
        return RiskDecision(
            allowed=allowed,
            effect=rule.effect,
            risk_level=rule.risk_level,
            rule_id=rule.rule_id,
            message=rule.description or f"Matched rule {rule.rule_id}",
        )

    return RiskDecision(
        allowed=False,
        effect=RiskEffect.REQUIRE_HITL,
        risk_level=RiskLevel.L1,
        rule_id="default_l1",
        message="No explicit rule; default L1 human review required",
    )


def default_production_rule_set() -> RiskRuleSet:
    """Baseline rules from 10_MANAGER_VISION_PLAN §6."""
    return RiskRuleSet(
        version="1.0",
        rules=[
            RiskRule(
                rule_id="l0_research_read",
                action=RiskAction.RESEARCH_READ,
                risk_level=RiskLevel.L0,
                effect=RiskEffect.ALLOW,
                description="Read-only research is auto allowed.",
                priority=10,
            ),
            RiskRule(
                rule_id="l0_listing_generate",
                action=RiskAction.LISTING_GENERATE,
                risk_level=RiskLevel.L0,
                effect=RiskEffect.ALLOW,
                description="Draft generation is auto allowed with trace.",
                priority=20,
            ),
            RiskRule(
                rule_id="l1_listing_publish",
                action=RiskAction.LISTING_PUBLISH,
                risk_level=RiskLevel.L1,
                effect=RiskEffect.REQUIRE_HITL,
                description="Listing publish requires human approval.",
                priority=30,
            ),
            RiskRule(
                rule_id="l1_price_update",
                action=RiskAction.PRICE_UPDATE,
                risk_level=RiskLevel.L1,
                effect=RiskEffect.REQUIRE_HITL,
                description="Price changes require human approval.",
                priority=40,
            ),
            RiskRule(
                rule_id="l1_ads_bid",
                action=RiskAction.ADS_BID_CHANGE,
                risk_level=RiskLevel.L1,
                effect=RiskEffect.REQUIRE_HITL,
                description="Ad bid changes require human approval.",
                priority=50,
            ),
            RiskRule(
                rule_id="l1_ads_budget",
                action=RiskAction.ADS_BUDGET_CHANGE,
                risk_level=RiskLevel.L1,
                effect=RiskEffect.REQUIRE_HITL,
                description="Ad budget changes require human approval.",
                priority=60,
            ),
            RiskRule(
                rule_id="l2_new_account_open",
                action=RiskAction.ACCOUNT_OPEN,
                risk_level=RiskLevel.L2,
                effect=RiskEffect.DENY,
                description="New ad account opening is suggest-only.",
                priority=70,
            ),
            RiskRule(
                rule_id="l2_high_budget",
                action=RiskAction.ADS_BUDGET_CHANGE,
                risk_level=RiskLevel.L2,
                effect=RiskEffect.DENY,
                description="Budget above threshold is denied pending review.",
                conditions=[RiskCondition(field="daily_budget", operator="gt", value=10_000)],
                priority=5,
            ),
        ],
    )
