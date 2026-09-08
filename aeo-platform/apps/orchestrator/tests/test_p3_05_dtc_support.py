"""P3-05 acceptance tests — DTC Customer Support Integration."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_shopify_scripts_in_library() -> None:
    from aeo_shared.after_sales_scripts import get_script_library

    library = get_script_library()
    shopify_scripts = library.filter_by(platform="shopify")
    assert len(shopify_scripts) >= 3

    scenarios = {s.scenario for s in shopify_scripts}
    assert "abandoned_cart" in scenarios
    assert "shipping" in scenarios
    assert "discount_issue" in scenarios


def test_shopify_abandoned_cart_script_content() -> None:
    from aeo_shared.after_sales_scripts import get_script_library

    library = get_script_library()
    script = library.get_best(scenario="abandoned_cart", platform="shopify")
    assert script is not None
    assert script.script_id == "shopify-abandoned-cart-001"
    assert "COMEBACK10" in script.template_text
    assert "cart" in script.template_text.lower()


def test_shopify_discount_issue_script_content() -> None:
    from aeo_shared.after_sales_scripts import get_script_library

    library = get_script_library()
    script = library.get_best(scenario="discount_issue", platform="shopify")
    assert script is not None
    assert script.script_id == "shopify-discount-001"
    assert "discount" in script.template_text.lower()


def test_detect_scenario_dtc_abandoned_cart() -> None:
    from aeo_orchestrator.nodes.support import _detect_scenario

    parsed = {"reply_draft": "We noticed you abandoned cart items"}
    assert _detect_scenario(parsed, []) == "abandoned_cart"


def test_detect_scenario_dtc_discount_issue() -> None:
    from aeo_orchestrator.nodes.support import _detect_scenario

    parsed = {"reply_draft": "Your promo code has expired"}
    assert _detect_scenario(parsed, []) == "discount_issue"


def test_detect_scenario_dtc_coupon() -> None:
    from aeo_orchestrator.nodes.support import _detect_scenario

    parsed = {"reply_draft": "The coupon code didn't apply"}
    assert _detect_scenario(parsed, []) == "discount_issue"


@pytest.mark.asyncio
async def test_support_node_shopify_platform_routes() -> None:
    from aeo_orchestrator.nodes.support import support_node
    from aeo_orchestrator.state import initial_state

    state = initial_state(
        task_id="p3-05-shopify",
        platform="shopify",
        sku="DTC-TEE-001",
        product_info={"title": "Organic Tee", "price": 34.99},
    )

    mock_llm_response = json.dumps(
        {
            "reply_draft": "Thanks for reaching out about your Shopify order.",
            "confidence": "high",
            "requires_human_review": False,
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider),
        patch(
            "aeo_orchestrator.nodes.support._fetch_shopify_order_context",
            return_value=[{"product_id": "P001", "sku": "DTC-TEE-001"}],
        ),
        patch("aeo_orchestrator.nodes.support._search_rag", return_value=[]),
    ):
        result = await support_node(state)

    support = result["support"]
    assert "reply_draft" in support
    assert support["order_context"] == [{"product_id": "P001", "sku": "DTC-TEE-001"}]


@pytest.mark.asyncio
async def test_support_node_amazon_platform_still_works() -> None:
    from aeo_orchestrator.nodes.support import support_node
    from aeo_orchestrator.state import initial_state

    state = initial_state(
        task_id="p3-05-amazon",
        platform="amazon",
        sku="AMZ-001",
    )

    mock_llm_response = json.dumps(
        {
            "reply_draft": "Thanks for your Amazon inquiry.",
            "confidence": "medium",
            "requires_human_review": False,
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_llm_response, model="test")

    with (
        patch("aeo_orchestrator.nodes.support.get_llm_provider", return_value=mock_provider),
        patch(
            "aeo_orchestrator.nodes.support._fetch_order_context",
            return_value=[{"order_id": "A001", "sku": "AMZ-001"}],
        ),
        patch("aeo_orchestrator.nodes.support._search_rag", return_value=[]),
    ):
        result = await support_node(state)

    support = result["support"]
    assert support["order_context"] == [{"order_id": "A001", "sku": "AMZ-001"}]


def test_shopify_scripts_list_scenarios() -> None:
    from aeo_shared.after_sales_scripts import get_script_library

    library = get_script_library()
    scenarios = library.list_scenarios()
    assert "abandoned_cart" in scenarios
    assert "discount_issue" in scenarios


def test_shopify_scripts_list_platforms() -> None:
    from aeo_shared.after_sales_scripts import get_script_library

    library = get_script_library()
    platforms = library.list_platforms()
    assert "shopify" in platforms
    assert "amazon" in platforms
