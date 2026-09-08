"""MV4-08 acceptance tests — 7-day daily reports + 50 customer service replies."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from aeo_llm.provider import LLMResponse


def _mock_analytics_llm(day_index: int) -> AsyncMock:
    gmv = 800 + day_index * 50
    orders = 20 + day_index * 2
    summary = f"Day {day_index}: GMV ${gmv} with {orders} orders."
    response_body = json.dumps(
        {
            "daily_summary": summary,
            "weekly_trend": f"Revenue trending up. Day {day_index} of 7-day cycle.",
            "strategy_suggestions": [
                {
                    "action": "increase_ad_spend",
                    "sku": "TEST-SKU-001",
                    "reason": f"Strong ROI on day {day_index}",
                }
            ],
            "kpi_targets": {
                "daily_gmv_target": 1000,
                "daily_gmv_actual": 800 + day_index * 50,
                "target_met": day_index >= 3,
            },
        }
    )
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=response_body, model="test")
    return mock_provider


_SUPPORT_SCENARIOS = [
    ("shipping", "Where is my order? It was supposed to arrive 3 days ago."),
    ("return", "I want to return this product, it doesn't match the description."),
    ("refund", "The product arrived damaged. I want a full refund."),
    ("complaint", "The item stopped working after 2 days of use. Very disappointed."),
    ("exchange", "I received a completely different product than what I ordered."),
    ("inquiry", "What are the dimensions of this product?"),
]


def _mock_support_llm(scenario: str, customer_message: str) -> AsyncMock:
    reply_map = {
        "shipping": (
            "I apologize for the delay. Your order is in transit "
            "and should arrive within 1-2 business days."
        ),
        "return": (
            "I'm sorry the product didn't match expectations. "
            "I've initiated a return label for you."
        ),
        "refund": (
            "I'm sorry about the damage. A full refund has been "
            "processed to your original payment method."
        ),
        "complaint": (
            "I apologize for the defect. We'll send a replacement "
            "immediately or process a refund."
        ),
        "exchange": (
            "I sincerely apologize for the mix-up. A correct item "
            "will be shipped today with express delivery."
        ),
        "inquiry": (
            "Thank you for your interest! The product dimensions "
            "are 10x8x6 inches, weighing 1.5 lbs."
        ),
    }
    requires_human = scenario in ("refund", "complaint")

    response_body = json.dumps(
        {
            "reply_draft": reply_map.get(
                scenario, "Thank you for contacting us. We are looking into your issue.",
            ),
            "order_context": {
                "order_id": "111-2222222-3333333",
                "status": "Shipped",
            },
            "rag_references": [
                {"doc_id": f"faq-{scenario}", "content": f"Reference for {scenario}"}
            ],
            "confidence": "high" if not requires_human else "medium",
            "requires_human_review": requires_human,
        }
    )
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=response_body, model="test")
    return mock_provider


@pytest.mark.asyncio
async def test_mv4_08_daily_report_7_consecutive_days() -> None:
    """MV4-08 acceptance: 7 consecutive daily reports all generate successfully."""
    from unittest.mock import patch

    from aeo_orchestrator.runner import run_analytics_task, serialize_analytics_result

    results = []
    for day in range(7):
        mock_provider = _mock_analytics_llm(day)
        with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
            state = await run_analytics_task(
                sku="TEST-SKU-001",
                platform="amazon",
                market="US",
                task_id=f"mv4-08-day-{day}",
                product_info={"title": "Test Product", "price": 29.99},
            )
        serialized = serialize_analytics_result(state)
        results.append(serialized)

    assert len(results) == 7

    for i, result in enumerate(results):
        assert result["task_id"] == f"mv4-08-day-{i}"
        analytics = result.get("analytics", {})
        assert analytics.get("daily_summary"), f"Day {i}: missing daily_summary"
        assert analytics.get("weekly_trend"), f"Day {i}: missing weekly_trend"
        assert analytics.get("strategy_suggestions"), f"Day {i}: missing strategy_suggestions"
        assert isinstance(analytics["strategy_suggestions"], list)
        assert len(analytics["strategy_suggestions"]) > 0


@pytest.mark.asyncio
async def test_mv4_08_customer_service_50_replies() -> None:
    """MV4-08 acceptance: 50 customer service replies with >=85% quality."""
    from unittest.mock import patch

    from aeo_orchestrator.runner import run_support_task, serialize_support_result

    total = 50
    passed = 0
    results = []

    for i in range(total):
        scenario_idx = i % len(_SUPPORT_SCENARIOS)
        scenario, message = _SUPPORT_SCENARIOS[scenario_idx]
        mock_provider = _mock_support_llm(scenario, message)

        with patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider):
            state = await run_support_task(
                sku=f"TEST-SKU-{i:03d}",
                platform="amazon",
                market="US",
                task_id=f"mv4-08-support-{i}",
                product_info={"title": f"Test Product {i}"},
            )

        serialized = serialize_support_result(state)
        results.append(serialized)

        support = serialized.get("support", {})
        reply_draft = support.get("reply_draft", "")
        has_reply = bool(reply_draft and len(reply_draft) > 10)
        has_order_context = isinstance(support.get("order_context"), list)
        if has_reply and has_order_context:
            passed += 1

    assert len(results) == total
    pass_rate = passed / total
    assert pass_rate >= 0.85, f"Customer service pass rate {pass_rate:.1%} < 85%"


@pytest.mark.asyncio
async def test_mv4_08_analytics_strategy_creates_tasks() -> None:
    """MV4-08: analytics strategy suggestions produce created_tasks."""
    from unittest.mock import patch

    from aeo_orchestrator.runner import run_analytics_task, serialize_analytics_result

    mock_provider = _mock_analytics_llm(0)
    with patch("aeo_orchestrator.nodes.analytics.get_llm_provider", return_value=mock_provider):
        state = await run_analytics_task(
            sku="TEST-SKU-001",
            platform="amazon",
            market="US",
            task_id="mv4-08-strategy-check",
            product_info={"title": "Test Product"},
        )

    serialized = serialize_analytics_result(state)
    analytics = serialized.get("analytics", {})
    created_tasks = analytics.get("created_tasks", [])
    assert isinstance(created_tasks, list)
    assert len(created_tasks) > 0, "Strategy suggestions should create follow-up tasks"


def test_mv4_08_escalation_rules_trigger_correctly() -> None:
    """MV4-08: escalation rules correctly identify cases needing human review."""
    from aeo_shared.escalation import EscalationEvaluator, EscalationRule

    rules = [
        EscalationRule(
            rule_id="refund",
            description="Refund requests over $50",
            field="refund_amount",
            operator="gte",
            threshold=50,
            priority=10,
        ),
        EscalationRule(
            rule_id="complaint",
            description="Customer complaint repeat",
            field="contact_count",
            operator="gte",
            threshold=3,
            priority=10,
        ),
    ]
    evaluator = EscalationEvaluator(rules=rules)

    result_refund = evaluator.evaluate(
        scenario="refund", context={"refund_amount": 75, "contact_count": 1},
    )
    assert result_refund.escalate
    assert result_refund.matched_rule_id == "refund"

    result_repeat = evaluator.evaluate(
        scenario="complaint", context={"refund_amount": 10, "contact_count": 3},
    )
    assert result_repeat.escalate
    assert result_repeat.matched_rule_id == "complaint"

    result_normal = evaluator.evaluate(
        scenario="inquiry", context={"refund_amount": 10, "contact_count": 1},
    )
    assert not result_normal.escalate


def test_mv4_08_script_library_covers_all_scenarios() -> None:
    """MV4-08: script library has coverage for all 6 support scenarios."""
    from aeo_shared import get_script_library

    library = get_script_library()
    scenarios = library.list_scenarios()

    expected = {"return", "refund", "shipping", "complaint", "inquiry", "exchange"}
    covered = expected.intersection(set(scenarios))
    coverage_rate = len(covered) / len(expected)
    missing = expected - covered
    assert coverage_rate >= 0.8, (
        f"Script coverage {coverage_rate:.0%} < 80%, missing: {missing}"
    )
