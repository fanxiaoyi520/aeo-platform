"""research_agent — S3-02 no-browser + MS4 optional Playwright enrichment."""

from __future__ import annotations

import json
import re

from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event
from aeo_orchestrator.tools.amazon_listing import enrich_product_info_from_amazon

MAX_BROWSER_FETCHES = 5


def _parse_competitors(product_info: dict[str, object]) -> list[dict[str, str]]:
    competitors: list[dict[str, str]] = []
    raw_asins = product_info.get("competitor_asins") or product_info.get("competitors")
    if isinstance(raw_asins, str):
        raw_asins = [a.strip() for a in re.split(r"[\s,;]+", raw_asins) if a.strip()]
    if isinstance(raw_asins, list):
        for item in raw_asins:
            if isinstance(item, str):
                competitors.append({"asin": item, "source": "user_input"})
            elif isinstance(item, dict) and item.get("asin"):
                competitors.append(
                    {
                        "asin": str(item["asin"]),
                        "title": str(item.get("title", "")),
                        "source": str(item.get("source", "user_input")),
                    }
                )
    notes = product_info.get("competitor_notes")
    if isinstance(notes, str) and notes.strip():
        competitors.append({"asin": "", "notes": notes.strip(), "source": "user_notes"})
    return competitors


def _baseline_keywords(state: TaskState) -> list[str]:
    product_info = state.get("product_info") or {}
    keywords: list[str] = []
    for key in ("keywords", "search_terms"):
        raw = product_info.get(key)
        if isinstance(raw, list):
            keywords.extend(str(k) for k in raw if k)
        elif isinstance(raw, str) and raw.strip():
            keywords.extend(part for part in raw.split(",") if part.strip())
    if not keywords:
        keywords = [state["sku"], str(product_info.get("category", "OBD2 diagnostic"))]
    return keywords


async def _enrich_competitors_with_browser(
    competitors: list[dict[str, str]],
    *,
    market: str,
) -> tuple[list[dict[str, str]], bool]:
    """Fetch public listing pages when browser automation is enabled."""
    try:
        from aeo_browser import fetch_listing, is_browser_enabled
    except ImportError:
        return competitors, False

    if not is_browser_enabled():
        return competitors, False

    enriched: list[dict[str, str]] = []
    fetch_failures = 0
    for item in competitors[:MAX_BROWSER_FETCHES]:
        asin = item.get("asin", "").strip()
        if not asin:
            enriched.append(item)
            continue
        try:
            listing = await fetch_listing(asin, market=market)
            merged = {**item, **{k: str(v) for k, v in listing.items() if v is not None}}
            merged["source"] = "browser"
            enriched.append(merged)
        except Exception:
            fetch_failures += 1
            fallback = {**item, "source": item.get("source", "user_input")}
            enriched.append(fallback)

    asin_items = [c for c in competitors if c.get("asin")]
    degraded = fetch_failures > 0 and fetch_failures == len(asin_items)
    return enriched, degraded


async def _expand_keywords_with_llm(state: TaskState, keywords: list[str]) -> list[str]:
    from aeo_llm.openai_compatible import get_llm_provider

    product_info = state.get("product_info") or {}
    prompt = (
        f"Platform: {state.get('platform')}\n"
        f"SKU: {state.get('sku')}\n"
        f"Product: {json.dumps(product_info, ensure_ascii=False)}\n"
        "Suggest up to 8 Amazon search keywords as a JSON array of strings only."
    )
    provider = get_llm_provider()
    response = await provider.chat(
        [
            Message(role="system", content="You output JSON arrays only."),
            Message(role="user", content=prompt),
        ],
        temperature=0.2,
    )
    text = response.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return [str(k) for k in parsed if k]
    return keywords


async def research_node(state: TaskState) -> dict[str, object]:
    """research_agent — user input + optional browser fetch + LLM keyword expansion."""
    trace = [with_started_trace(state, "research_agent")]
    product_info, amazon_listing = enrich_product_info_from_amazon(
        sku=state["sku"],
        market=str(state.get("market", "US")),
        platform=str(state.get("platform", "amazon")),
        product_info=dict(state.get("product_info") or {}),
    )
    competitors = _parse_competitors(product_info)
    keywords = _baseline_keywords({**state, "product_info": product_info})
    degraded = False
    market = str(state.get("market", "US"))

    if competitors:
        competitors, browser_degraded = await _enrich_competitors_with_browser(
            competitors,
            market=market,
        )
        degraded = degraded or browser_degraded
        trace.append(
            make_trace_event(
                "research_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "competitor_count": len(competitors),
                    "keyword_count": len(keywords),
                    "browser_enriched": any(c.get("source") == "browser" for c in competitors),
                    "degraded": degraded,
                },
            )
        )
    else:
        degraded = True
        try:
            keywords = await _expand_keywords_with_llm(state, keywords)
        except Exception as exc:
            trace.append(
                make_trace_event(
                    "research_agent",
                    AgentTraceStatus.FAILED,
                    detail={"degraded": True, "error": str(exc)},
                )
            )
        else:
            trace.append(
                make_trace_event(
                    "research_agent",
                    AgentTraceStatus.COMPLETED,
                    detail={"degraded": True, "keyword_count": len(keywords)},
                )
            )

    return {
        "product_info": product_info,
        "research": {
            "competitors": competitors,
            "keywords": keywords,
            "degraded": degraded,
            "amazon_listing_loaded": amazon_listing is not None,
        },
        "degraded_mode": degraded or state.get("degraded_mode", False),
        "trace": trace,
    }
