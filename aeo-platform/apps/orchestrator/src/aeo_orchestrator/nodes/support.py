"""support_agent — MV4-02/03 customer service reply drafts with RAG + order context + script library + escalation."""

from __future__ import annotations

import json
from typing import Any

from aeo_integrations.amazon.orders import get_orders_client
from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message
from aeo_shared.after_sales_scripts import get_script_library
from aeo_shared.escalation import EscalationEvaluator
from aeo_shared.order_ingest import OrderIngestService

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


def _get_knowledge_store() -> Any:
    import os

    from aeo_rag.store import KnowledgeStore

    use_hash = os.environ.get("RAG_HASH_EMBEDDINGS", "").lower() in ("1", "true", "yes")
    return KnowledgeStore(use_hash_embeddings=use_hash)


def _search_rag(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    try:
        store = _get_knowledge_store()
        results = store.search(
            query=query,
            category="customer-service",
            top_k=top_k,
            score_threshold=0.5,
        )
        return [
            {
                "doc_id": r.doc_id,
                "content": r.content,
                "score": r.score,
            }
            for r in results
        ]
    except Exception:
        return []


def _fetch_order_context(sku: str, limit: int = 5) -> list[dict[str, Any]]:
    try:
        client = get_orders_client()
        ingest = OrderIngestService()
        records = ingest.ingest_amazon(client, sku=sku, limit=limit)
        return [
            {
                "order_id": r.external_order_id,
                "sku": r.sku,
                "order_status": r.order_status,
                "tracking_number": r.tracking_number,
                "carrier": r.carrier,
                "purchase_date": r.purchase_date,
            }
            for r in records
        ]
    except Exception:
        return []


def _build_user_prompt(
    state: TaskState,
    order_context: list[dict[str, Any]],
    rag_references: list[dict[str, Any]],
    matched_script: dict[str, Any] | None = None,
) -> str:
    sku = state.get("sku", "")
    product_info = state.get("product_info") or {}

    script_section = ""
    if matched_script:
        script_section = (
            f"Matching reply template:\n{json.dumps(matched_script, indent=2)}\n\n"
        )

    return (
        f"You are a customer service specialist.\n"
        f"Primary SKU: {sku}\n"
        f"Product: {product_info.get('title', 'N/A')}\n\n"
        f"Order context:\n{json.dumps(order_context, indent=2)}\n\n"
        f"Knowledge base references:\n{json.dumps(rag_references, indent=2)}\n\n"
        f"{script_section}"
        "Generate a customer reply draft in JSON format:\n"
        '{"reply_draft": "customer-facing reply text", '
        '"confidence": "high|medium|low", '
        '"requires_human_review": true/false}'
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
            "reply_draft": text,
            "confidence": "low",
            "requires_human_review": True,
        }


def _detect_scenario(parsed: dict[str, Any], order_context: list[dict[str, Any]]) -> str:
    reply = parsed.get("reply_draft", "").lower()
    for keyword_scenario in [
        ("refund", "refund"),
        ("return", "return"),
        ("shipping", "shipping"),
        ("delivery", "shipping"),
        ("track", "shipping"),
        ("complaint", "complaint"),
        ("defective", "complaint"),
        ("exchange", "exchange"),
        ("replace", "exchange"),
    ]:
        keyword, scenario = keyword_scenario
        if keyword in reply:
            return scenario
    return "inquiry"


async def support_node(state: TaskState) -> dict[str, object]:
    """support_agent — generate customer service reply drafts using RAG + order data + script library + escalation."""
    trace = [with_started_trace(state, "support_agent")]

    try:
        sku = state.get("sku", "")
        platform = state.get("platform", "amazon")

        order_context = _fetch_order_context(sku)
        rag_query = f"customer service {sku} order status shipping return"
        rag_references = _search_rag(rag_query)

        library = get_script_library()
        all_scripts = library.filter_by(platform=platform)
        default_script = all_scripts[0].to_dict() if all_scripts else None

        prompt = _build_user_prompt(state, order_context, rag_references, default_script)
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(
                    role="system",
                    content=(
                        "You are a customer service specialist. "
                        "Generate professional, helpful reply drafts for customer inquiries. "
                        "Use the order context, knowledge base references, and reply template provided. "
                        "Output valid JSON only."
                    ),
                ),
                Message(role="user", content=prompt),
            ],
            temperature=0.3,
        )

        parsed = _parse_llm_json(response.content)

        scenario = _detect_scenario(parsed, order_context)
        matched = library.get_best(scenario=scenario, platform=platform)
        matched_script = matched.to_dict() if matched else None

        evaluator = EscalationEvaluator()
        escalation_ctx: dict[str, Any] = {}
        if parsed.get("refund_amount") is not None:
            escalation_ctx["refund_amount"] = parsed["refund_amount"]
        if parsed.get("severity") is not None:
            escalation_ctx["severity"] = parsed["severity"]
        escalation_ctx["repeat_count"] = parsed.get("repeat_count", 0)
        escalation_result = evaluator.evaluate(scenario=scenario, context=escalation_ctx)

        requires_review = escalation_result.escalate or parsed.get("requires_human_review", False)

        result = {
            "reply_draft": parsed.get("reply_draft", ""),
            "order_context": order_context,
            "rag_references": rag_references,
            "matched_script": matched_script,
            "escalation": escalation_result.to_dict(),
            "confidence": parsed.get("confidence", "medium"),
            "requires_human_review": requires_review,
        }

        trace.append(
            make_trace_event(
                "support_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "order_count": len(order_context),
                    "rag_reference_count": len(rag_references),
                    "scenario": scenario,
                    "matched_script_id": matched.script_id if matched else None,
                    "escalate": escalation_result.escalate,
                    "confidence": result["confidence"],
                    "requires_human_review": requires_review,
                },
            )
        )

    except Exception as exc:
        result = {
            "reply_draft": f"Support reply generation failed: {exc}",
            "order_context": [],
            "rag_references": [],
            "matched_script": None,
            "escalation": {"escalate": True, "reason": f"Error: {exc}", "matched_rule_id": None},
            "confidence": "low",
            "requires_human_review": True,
            "error": str(exc),
        }
        trace.append(
            make_trace_event(
                "support_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"support": result, "trace": trace}
