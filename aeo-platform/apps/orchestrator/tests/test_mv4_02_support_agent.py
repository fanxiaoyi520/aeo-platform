"""MV4-02 acceptance tests — A05 Support Agent end-to-end."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_support_agent_active_in_registry() -> None:
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    agent = registry.get("support_agent")
    assert agent.status == "active"
    assert agent.graph_node == "support"
    assert agent.category.value == "A05"
    assert agent.risk_level.value == "L1"
    capability_names = [c.name for c in agent.capabilities]
    assert "support.reply_draft" in capability_names


def test_support_subgraph_registered() -> None:
    from aeo_shared import get_subgraph

    graph = get_subgraph("support")
    assert graph.graph_id == "support"
    assert "support_agent" in graph.agent_ids


def test_support_graph_builds() -> None:
    from aeo_orchestrator.graph import build_support_graph

    graph = build_support_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_support_graph_e2e() -> None:
    from aeo_orchestrator.graph import build_support_graph
    from aeo_orchestrator.state import initial_state

    graph = build_support_graph()
    state = initial_state(
        task_id="mv4-02-e2e",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={
            "title": "HomeBrew Electric Kettle 1L",
            "price": 29.99,
            "category": "Home & Kitchen",
        },
    )

    mock_llm_response = json.dumps(
        {
            "reply_draft": "Thank you for your inquiry. Your order is being processed.",
            "order_context": {
                "order_id": "111-0000000-0000001",
                "status": "Shipped",
            },
            "rag_references": [
                {"doc_id": "faq-001", "content": "Shipping takes 3-5 business days."}
            ],
            "confidence": "high",
            "requires_human_review": False,
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "mv4-02-e2e"}}
        )

    support = result.get("support")
    assert support is not None
    assert "reply_draft" in support
    assert "order_context" in support
    assert "rag_references" in support
    assert "confidence" in support
    assert "requires_human_review" in support

    assert isinstance(support["reply_draft"], str)
    assert len(support["reply_draft"]) > 0

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "support_agent"]
    assert len(agent_events) >= 2
    assert agent_events[0]["status"] == "started"
    assert agent_events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_run_support_task() -> None:
    from aeo_orchestrator.runner import run_support_task

    mock_llm_response = json.dumps(
        {
            "reply_draft": "Your order has shipped.",
            "order_context": {},
            "rag_references": [],
            "confidence": "high",
            "requires_human_review": False,
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider):
        result = await run_support_task(
            sku="HOMEBREW-KETTLE-1L",
            product_info={"title": "Electric Kettle", "price": 29.99},
            task_id="runner-support-1",
        )

    assert result["task_id"] == "runner-support-1"
    assert result["support"] is not None


def test_support_agent_in_graph_catalog() -> None:
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "support" in catalog
