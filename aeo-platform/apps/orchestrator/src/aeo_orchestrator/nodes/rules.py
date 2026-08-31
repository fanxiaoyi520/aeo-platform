"""rules_agent — S3-03: RAG search for platform rules, product docs, and examples."""

from __future__ import annotations

from aeo_rag.store import KnowledgeStore, SearchResult

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


def _get_knowledge_store() -> KnowledgeStore:
    import os

    use_hash = os.environ.get("RAG_USE_HASH_EMBEDDINGS", "false").lower() == "true"
    return KnowledgeStore(use_hash_embeddings=use_hash)


def _reference_from_hit(hit: SearchResult) -> dict[str, object]:
    return {
        "doc_id": hit.doc_id,
        "content": hit.content,
        "score": hit.score,
        "category": hit.category,
        "platform": hit.platform,
        "source_file": hit.source_file,
        "chunk_index": hit.chunk_index,
    }


def _dedupe_hits(hits: list[SearchResult]) -> list[SearchResult]:
    seen: set[tuple[str, int]] = set()
    unique: list[SearchResult] = []
    for hit in hits:
        key = (hit.doc_id, hit.chunk_index)
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique


def _build_rule_summary(rule_hits: list[SearchResult], product_hits: list[SearchResult]) -> str:
    parts: list[str] = []
    for hit in rule_hits[:3]:
        snippet = hit.content.strip().replace("\n", " ")
        if snippet:
            parts.append(snippet[:240])
    if product_hits:
        snippet = product_hits[0].content.strip().replace("\n", " ")
        if snippet:
            parts.append(f"Product: {snippet[:200]}")
    return "\n".join(parts)


def _search_rules(
    store: KnowledgeStore,
    *,
    platform: str,
    sku: str,
    category: str,
    keywords: list[str],
) -> dict[str, object]:
    keyword_text = " ".join(str(k) for k in keywords[:5])
    rule_query = f"{platform} listing title bullet search terms rules {category}"
    product_query = f"{sku} {category} product specifications features"
    example_query = f"{platform} listing example {keyword_text}".strip()

    rule_hits = store.search(rule_query, platform=platform, score_threshold=0.0)
    product_hits = store.search(product_query, category="product", score_threshold=0.0)
    example_hits = store.search(
        example_query,
        platform=platform,
        category="example",
        score_threshold=0.0,
    )

    combined = _dedupe_hits(rule_hits + product_hits + example_hits)
    references = [_reference_from_hit(hit) for hit in combined]
    return {
        "platform": platform,
        "rule_summary": _build_rule_summary(rule_hits, product_hits),
        "references": references,
        "product_snippets": [_reference_from_hit(hit) for hit in product_hits[:3]],
        "example_snippets": [_reference_from_hit(hit) for hit in example_hits[:2]],
    }


async def rules_node(state: TaskState) -> dict[str, object]:
    """rules_agent — queries knowledge base for platform rules and product context."""
    trace = [with_started_trace(state, "rules_agent")]
    platform = state.get("platform", "amazon")
    product_info = state.get("product_info") or {}
    research = state.get("research") or {}
    keywords: list[str] = []
    if isinstance(research, dict):
        raw_keywords = research.get("keywords")
        if isinstance(raw_keywords, list):
            keywords = [str(k) for k in raw_keywords if k]

    category = str(product_info.get("category", "OBD2 diagnostic"))
    sku = state.get("sku", "")

    try:
        rules_payload = _search_rules(
            _get_knowledge_store(),
            platform=platform,
            sku=sku,
            category=category,
            keywords=keywords,
        )
        references = rules_payload["references"]
        trace.append(
            make_trace_event(
                "rules_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "reference_count": len(references) if isinstance(references, list) else 0,
                    "has_summary": bool(rules_payload.get("rule_summary")),
                },
            )
        )
    except Exception as exc:
        rules_payload = {
            "platform": platform,
            "rule_summary": "",
            "references": [],
            "product_snippets": [],
            "example_snippets": [],
            "error": str(exc),
        }
        trace.append(
            make_trace_event(
                "rules_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"rules": rules_payload, "trace": trace}
