"""MV4-03 acceptance tests — support_node integration with script library + escalation."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


@pytest.mark.asyncio
async def test_support_node_uses_script_library() -> None:
    from aeo_orchestrator.graph import build_support_graph
    from aeo_orchestrator.state import initial_state

    graph = build_support_graph()
    state = initial_state(
        task_id="mv4-03-script-lib",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={"title": "Electric Kettle", "price": 29.99},
    )

    mock_llm_response = json.dumps(
        {
            "reply_draft": "Your return has been processed.",
            "confidence": "high",
            "requires_human_review": False,
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider),
    ):
        result = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "mv4-03-script-lib"}}
        )

    support = result.get("support")
    assert support is not None
    assert "matched_script" in support


@pytest.mark.asyncio
async def test_support_node_escalation_driven_by_rules() -> None:
    from aeo_orchestrator.graph import build_support_graph
    from aeo_orchestrator.state import initial_state

    graph = build_support_graph()
    state = initial_state(
        task_id="mv4-03-escalation",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={"title": "Electric Kettle", "price": 29.99},
    )

    mock_llm_response = json.dumps(
        {
            "reply_draft": "Refund processed.",
            "confidence": "high",
            "requires_human_review": False,
            "refund_amount": 100.0,
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider),
    ):
        result = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "mv4-03-escalation"}}
        )

    support = result.get("support")
    assert support is not None
    assert "escalation" in support
    assert support["escalation"]["escalate"] is True


@pytest.mark.asyncio
async def test_support_node_low_refund_no_escalation() -> None:
    from aeo_orchestrator.graph import build_support_graph
    from aeo_orchestrator.state import initial_state

    graph = build_support_graph()
    state = initial_state(
        task_id="mv4-03-no-escalation",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={"title": "Electric Kettle", "price": 29.99},
    )

    mock_llm_response = json.dumps(
        {
            "reply_draft": "Thank you for your inquiry.",
            "confidence": "high",
            "requires_human_review": False,
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider),
    ):
        result = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "mv4-03-no-escalation"}}
        )

    support = result.get("support")
    assert support is not None
    assert "escalation" in support
    assert support["escalation"]["escalate"] is False
