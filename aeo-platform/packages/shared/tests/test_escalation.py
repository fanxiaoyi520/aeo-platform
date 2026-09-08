"""MV4-03 acceptance tests — EscalationRule + EscalationEvaluator."""

from __future__ import annotations


def test_escalation_rule_dataclass() -> None:
    from aeo_shared.escalation import EscalationRule

    rule = EscalationRule(
        rule_id="refund-high-amount",
        description="Refund amount over $50 requires human review",
        field="refund_amount",
        operator="gt",
        threshold=50.0,
    )
    assert rule.rule_id == "refund-high-amount"
    assert rule.field == "refund_amount"
    assert rule.operator == "gt"
    assert rule.threshold == 50.0


def test_escalation_evaluator_refund_amount() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="refund",
        context={"refund_amount": 75.0, "order_total": 100.0},
    )
    assert result.escalate is True
    assert "refund" in result.reason.lower() or "amount" in result.reason.lower()


def test_escalation_evaluator_low_refund_no_escalation() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="refund",
        context={"refund_amount": 10.0, "order_total": 50.0},
    )
    assert result.escalate is False


def test_escalation_evaluator_complaint_severity() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="complaint",
        context={"severity": "high", "repeat_count": 1},
    )
    assert result.escalate is True


def test_escalation_evaluator_repeat_customer_issues() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="inquiry",
        context={"repeat_count": 4},
    )
    assert result.escalate is True


def test_escalation_evaluator_simple_inquiry_no_escalation() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="inquiry",
        context={"repeat_count": 0},
    )
    assert result.escalate is False


def test_escalation_evaluator_result_has_reason() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="refund",
        context={"refund_amount": 100.0},
    )
    assert isinstance(result.reason, str)
    assert len(result.reason) > 0


def test_escalation_evaluator_result_has_matched_rule() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="refund",
        context={"refund_amount": 100.0},
    )
    assert result.matched_rule_id is not None


def test_escalation_evaluator_no_match_returns_default() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="inquiry",
        context={},
    )
    assert result.escalate is False
    assert result.matched_rule_id is None


def test_escalation_result_to_dict() -> None:
    from aeo_shared.escalation import EscalationEvaluator

    evaluator = EscalationEvaluator()
    result = evaluator.evaluate(
        scenario="refund",
        context={"refund_amount": 100.0},
    )
    d = result.to_dict()
    assert "escalate" in d
    assert "reason" in d
    assert "matched_rule_id" in d
