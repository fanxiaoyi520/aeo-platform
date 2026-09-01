"""Tests for MV1-04 risk rule DSL."""

from __future__ import annotations

from aeo_shared.agent_registry import RiskLevel
from aeo_shared.risk_dsl import (
    RiskAction,
    RiskEffect,
    default_production_rule_set,
    evaluate_action,
)


def test_research_read_is_l0_allow() -> None:
    rules = default_production_rule_set()
    decision = evaluate_action(RiskAction.RESEARCH_READ, {}, rules)
    assert decision.allowed is True
    assert decision.effect == RiskEffect.ALLOW
    assert decision.risk_level == RiskLevel.L0


def test_listing_publish_requires_hitl() -> None:
    rules = default_production_rule_set()
    decision = evaluate_action(RiskAction.LISTING_PUBLISH, {}, rules)
    assert decision.allowed is False
    assert decision.effect == RiskEffect.REQUIRE_HITL
    assert decision.risk_level == RiskLevel.L1


def test_high_budget_change_is_denied() -> None:
    rules = default_production_rule_set()
    decision = evaluate_action(
        RiskAction.ADS_BUDGET_CHANGE,
        {"daily_budget": 15_000},
        rules,
    )
    assert decision.allowed is False
    assert decision.effect == RiskEffect.DENY
    assert decision.rule_id == "l2_high_budget"


def test_normal_budget_change_requires_hitl() -> None:
    rules = default_production_rule_set()
    decision = evaluate_action(
        RiskAction.ADS_BUDGET_CHANGE,
        {"daily_budget": 500},
        rules,
    )
    assert decision.effect == RiskEffect.REQUIRE_HITL
    assert decision.rule_id == "l1_ads_budget"


def test_unmapped_action_defaults_to_l1() -> None:
    rules = default_production_rule_set()
    decision = evaluate_action(RiskAction.ORDER_REFUND, {}, rules)
    assert decision.rule_id == "default_l1"
    assert decision.effect == RiskEffect.REQUIRE_HITL
