"""P3-02 acceptance tests — DTC Content Agent end-to-end."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_dtc_content_agent_active_in_registry() -> None:
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    agent = registry.get("dtc_content_agent")
    assert agent.status == "active"
    assert agent.graph_node is None
    assert agent.category.value == "A03"
    capability_names = [c.name for c in agent.capabilities]
    assert "generate.dtc_content" in capability_names
    assert agent.platforms == ["shopify"]


def test_dtc_content_subgraph_registered() -> None:
    from aeo_shared import get_subgraph

    graph = get_subgraph("dtc_content")
    assert graph.graph_id == "dtc_content"
    assert "dtc_content_agent" in graph.agent_ids


def test_dtc_content_graph_builds() -> None:
    from aeo_orchestrator.graph import build_dtc_content_graph

    graph = build_dtc_content_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_dtc_content_graph_e2e() -> None:
    from aeo_orchestrator.graph import build_dtc_content_graph
    from aeo_orchestrator.state import initial_state

    graph = build_dtc_content_graph()
    state = initial_state(
        task_id="p3-02-e2e",
        platform="shopify",
        sku="DTC-ORGANIC-TEE",
        product_info={
            "title": "Organic Cotton Tee",
            "price": 34.99,
            "product_type": "Apparel",
        },
    )

    mock_llm_response = json.dumps(
        {
            "landing_page": {
                "hero_headline": "Sustainable Style, Delivered",
                "subheadline": "Organic cotton tees that feel as good as they look.",
                "cta_text": "Shop Now",
                "body_paragraph": "Crafted from 100% GOTS-certified organic cotton.",
            },
            "email_campaign": {
                "subject": "Welcome to Conscious Fashion",
                "preview_text": "Your first order ships free.",
                "body": "Thanks for joining the movement...",
                "sequence": ["welcome", "abandoned_cart", "post_purchase"],
            },
            "social_posts": [
                {
                    "platform": "instagram",
                    "caption": "New drop alert 🌿",
                    "hashtags": ["#sustainablefashion", "#organiccotton"],
                },
                {
                    "platform": "facebook",
                    "caption": "Shop our latest organic collection.",
                },
            ],
            "report": "DTC content strategy focused on sustainability messaging.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with (
        patch("aeo_orchestrator.nodes.dtc_content.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_content.get_store_client") as mock_store,
    ):
        mock_store.return_value.list_products.return_value = []
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "p3-02-e2e"}})

    dtc = result.get("dtc_content")
    assert dtc is not None
    assert "landing_page" in dtc
    assert "email_campaign" in dtc
    assert "social_posts" in dtc
    assert "report" in dtc

    assert dtc["landing_page"]["hero_headline"] == "Sustainable Style, Delivered"
    assert len(dtc["social_posts"]) == 2
    assert dtc["email_campaign"]["sequence"] == ["welcome", "abandoned_cart", "post_purchase"]

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "dtc_content_agent"]
    assert len(agent_events) >= 2
    assert agent_events[0]["status"] == "started"
    assert agent_events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_dtc_content_node_handles_llm_failure() -> None:
    from aeo_orchestrator.nodes.dtc_content import dtc_content_node
    from aeo_orchestrator.state import initial_state

    state = initial_state(
        task_id="p3-02-fail",
        platform="shopify",
        sku="DTC-FAIL-001",
    )

    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = RuntimeError("LLM unavailable")

    with (
        patch("aeo_orchestrator.nodes.dtc_content.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_content.get_store_client") as mock_store,
    ):
        mock_store.return_value.list_products.return_value = []
        result = await dtc_content_node(state)

    dtc = result["dtc_content"]
    assert isinstance(dtc, dict)
    assert "error" in dtc
    assert "LLM unavailable" in dtc["error"]
    assert dtc["landing_page"] == {}


@pytest.mark.asyncio
async def test_run_dtc_content_task() -> None:
    from aeo_orchestrator.runner import run_dtc_content_task

    mock_llm_response = json.dumps(
        {
            "landing_page": {
                "hero_headline": "Test",
                "subheadline": "Sub",
                "cta_text": "Go",
                "body_paragraph": "Body",
            },
            "email_campaign": {
                "subject": "Hi",
                "preview_text": "Preview",
                "body": "Body",
                "sequence": [],
            },
            "social_posts": [],
            "report": "Test report",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.dtc_content.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.dtc_content.get_store_client") as mock_store,
    ):
        mock_store.return_value.list_products.return_value = []
        result = await run_dtc_content_task(
            sku="DTC-RUN-001",
            platform="shopify",
            product_info={"title": "Test Product", "price": 19.99},
            task_id="runner-dtc-1",
        )

    assert result["task_id"] == "runner-dtc-1"
    assert result["dtc_content"] is not None


def test_serialize_dtc_content_result() -> None:
    from aeo_orchestrator.runner import serialize_dtc_content_result
    from aeo_orchestrator.state import initial_state

    state = initial_state(task_id="ser-dtc", platform="shopify", sku="DTC-SER-001")
    state["dtc_content"] = {
        "landing_page": {"hero_headline": "Hello"},
        "email_campaign": {"subject": "Welcome"},
        "social_posts": [{"platform": "instagram", "caption": "Post"}],
        "report": "Summary",
    }

    serialized = serialize_dtc_content_result(state)
    assert serialized["task_id"] == "ser-dtc"
    assert serialized["sku"] == "DTC-SER-001"
    assert serialized["platform"] == "shopify"
    assert serialized["dtc_content"]["landing_page"]["hero_headline"] == "Hello"
    assert len(serialized["dtc_content"]["social_posts"]) == 1


def test_dtc_content_agent_in_graph_catalog() -> None:
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "dtc_content" in catalog


def test_dtc_content_node_importable() -> None:
    from aeo_orchestrator.nodes import dtc_content_node

    assert callable(dtc_content_node)


def test_dtc_content_parse_llm_json_handles_code_block() -> None:
    from aeo_orchestrator.nodes.dtc_content import _parse_llm_json

    code_block = '```json\n{"landing_page": {"hero_headline": "Test"}, "report": "ok"}\n```'
    parsed = _parse_llm_json(code_block)
    assert parsed["landing_page"]["hero_headline"] == "Test"
    assert parsed["report"] == "ok"


def test_dtc_content_parse_llm_json_handles_invalid_json() -> None:
    from aeo_orchestrator.nodes.dtc_content import _parse_llm_json

    parsed = _parse_llm_json("not json at all")
    assert parsed["landing_page"] == {
        "hero_headline": "",
        "subheadline": "",
        "cta_text": "",
        "body_paragraph": "",
    }
    assert parsed["report"] == "not json at all"
