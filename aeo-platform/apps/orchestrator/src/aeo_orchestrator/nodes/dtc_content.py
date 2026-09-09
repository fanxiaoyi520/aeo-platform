"""dtc_content_agent — P3-02 DTC landing page / email / social content generation."""

from __future__ import annotations

import json
from typing import Any

from aeo_integrations.shopify.store import get_store_client
from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


def _build_dtc_content_prompt(
    state: TaskState,
    shopify_products: list[dict[str, Any]],
) -> str:
    sku = state.get("sku", "")
    product_info = state.get("product_info") or {}

    return (
        f"You are a DTC (Direct-to-Consumer) content specialist for a Shopify store.\n"
        f"SKU: {sku}\n"
        f"Product: {product_info.get('title', 'N/A')}\n"
        f"Price: {product_info.get('price', 'N/A')}\n"
        f"Product type: {product_info.get('product_type', 'N/A')}\n\n"
        f"Store product catalog ({len(shopify_products)} products):\n"
        f"{json.dumps(shopify_products[:3], indent=2)}\n\n"
        "Generate DTC content in JSON format:\n"
        '{"landing_page": {"hero_headline": "...", "subheadline": "...", '
        '"cta_text": "...", "body_paragraph": "..."}, '
        '"email_campaign": {"subject": "...", "preview_text": "...", '
        '"body": "...", "sequence": ["welcome", "abandoned_cart", "post_purchase"]}, '
        '"social_posts": [{"platform": "instagram", "caption": "...", "hashtags": [...]}, '
        '{"platform": "facebook", "caption": "..."}], '
        '"report": "concise content strategy summary (3-5 sentences)"}'
    )


def _parse_llm_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        return {
            "landing_page": {
                "hero_headline": "",
                "subheadline": "",
                "cta_text": "",
                "body_paragraph": "",
            },
            "email_campaign": {"subject": "", "preview_text": "", "body": "", "sequence": []},
            "social_posts": [],
            "report": text,
        }


async def dtc_content_node(state: TaskState) -> dict[str, object]:
    """dtc_content_agent — generate DTC landing page, email, and social content."""
    trace = [with_started_trace(state, "dtc_content_agent")]

    try:
        store_client = get_store_client()
        products = store_client.list_products()
        product_dicts = [p.model_dump() for p in products]

        prompt = _build_dtc_content_prompt(state, product_dicts)
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(
                    role="system",
                    content=(
                        "You are a DTC content specialist for Shopify stores. "
                        "Generate compelling landing page copy, email campaigns, "
                        "and social media posts. Output valid JSON only."
                    ),
                ),
                Message(role="user", content=prompt),
            ],
            temperature=0.4,
        )

        parsed = _parse_llm_json(response.content)

        result = {
            "landing_page": parsed.get("landing_page", {}),
            "email_campaign": parsed.get("email_campaign", {}),
            "social_posts": parsed.get("social_posts", []),
            "report": parsed.get("report", ""),
        }

        trace.append(
            make_trace_event(
                "dtc_content_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "has_landing_page": bool(result["landing_page"]),
                    "has_email": bool(result["email_campaign"]),
                    "social_post_count": len(result["social_posts"]),
                },
            )
        )

    except Exception as exc:
        result = {
            "landing_page": {},
            "email_campaign": {},
            "social_posts": [],
            "report": f"DTC content generation failed: {exc}",
            "error": str(exc),
        }
        trace.append(
            make_trace_event(
                "dtc_content_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"dtc_content": result, "trace": trace}
