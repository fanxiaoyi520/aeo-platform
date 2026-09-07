"""MV4-03: Escalation rules engine for customer service triage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Operator = Literal["eq", "gt", "gte", "lt", "lte"]


@dataclass(frozen=True)
class EscalationRule:
    """A single escalation rule: if field <operator> threshold → escalate."""

    rule_id: str
    description: str
    field: str
    operator: Operator = "gt"
    threshold: Any = None
    scenarios: list[str] = field(default_factory=list)
    priority: int = 100


@dataclass(frozen=True)
class EscalationResult:
    """Result of evaluating escalation rules against a context."""

    escalate: bool
    reason: str
    matched_rule_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "escalate": self.escalate,
            "reason": self.reason,
            "matched_rule_id": self.matched_rule_id,
        }


def _match(op: Operator, actual: Any, threshold: Any) -> bool:
    if actual is None:
        return False
    if op == "eq":
        return actual == threshold
    if op == "gt":
        return actual > threshold
    if op == "gte":
        return actual >= threshold
    if op == "lt":
        return actual < threshold
    if op == "lte":
        return actual <= threshold
    return False


_DEFAULT_RULES: list[EscalationRule] = [
    EscalationRule(
        rule_id="refund-high-amount",
        description="Refund amount over $50 requires human review",
        field="refund_amount",
        operator="gt",
        threshold=50.0,
        scenarios=["refund", "return"],
        priority=10,
    ),
    EscalationRule(
        rule_id="complaint-high-severity",
        description="High-severity complaints require human review",
        field="severity",
        operator="eq",
        threshold="high",
        scenarios=["complaint"],
        priority=20,
    ),
    EscalationRule(
        rule_id="repeat-customer-issues",
        description="3+ repeat contacts from same customer require human review",
        field="repeat_count",
        operator="gte",
        threshold=3,
        scenarios=[],
        priority=30,
    ),
]


class EscalationEvaluator:
    """Evaluate escalation rules against a customer service context."""

    def __init__(self, rules: list[EscalationRule] | None = None) -> None:
        self._rules = sorted(
            rules if rules is not None else list(_DEFAULT_RULES),
            key=lambda r: r.priority,
        )

    def evaluate(
        self,
        *,
        scenario: str,
        context: dict[str, Any],
    ) -> EscalationResult:
        for rule in self._rules:
            if rule.scenarios and scenario not in rule.scenarios:
                continue
            actual = context.get(rule.field)
            if _match(rule.operator, actual, rule.threshold):
                return EscalationResult(
                    escalate=True,
                    reason=rule.description,
                    matched_rule_id=rule.rule_id,
                )

        return EscalationResult(
            escalate=False,
            reason="No escalation rules matched",
            matched_rule_id=None,
        )
