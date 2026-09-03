"""selection_agent — MV2-02 competitor analysis + scoring + report."""

from __future__ import annotations

import json

from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message
from aeo_shared.selection_scoring import (
    CompetitorData,
    SelectionInput,
    SelectionResult,
    score_product,
)

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


def _extract_competitors(product_info: dict[str, object]) -> list[CompetitorData]:
    competitors: list[CompetitorData] = []
    raw = product_info.get("competitors") or product_info.get("competitor_list")
    if not isinstance(raw, list):
        return competitors
    for item in raw:
        if not isinstance(item, dict):
            continue
        asin = str(item.get("asin", ""))
        if not asin:
            continue
        price = item.get("price")
        rating = item.get("rating")
        review_count = item.get("review_count")
        competitors.append(
            CompetitorData(
                asin=asin,
                price=float(price) if price is not None else None,
                rating=float(rating) if rating is not None else None,
                review_count=int(review_count) if review_count is not None else None,
            )
        )
    return competitors


def _build_selection_input(state: TaskState, competitors: list[CompetitorData]) -> SelectionInput:
    product_info = state.get("product_info") or {}
    return SelectionInput(
        sku=state["sku"],
        platform=str(state.get("platform", "amazon")),
        marketplace=str(state.get("market", "US")),
        price=_opt_float(product_info.get("price")),
        rating=_opt_float(product_info.get("rating")),
        review_count=_opt_int(product_info.get("review_count")),
        category=str(product_info.get("category", "")) or None,
        brand=str(product_info.get("brand", "")) or None,
        has_title=bool(product_info.get("title")),
        has_bullets=bool(product_info.get("bullet_points")),
        has_keywords=bool(product_info.get("keywords") or product_info.get("search_terms")),
        has_images=bool(product_info.get("images")),
        competitors=competitors,
    )


def _opt_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _opt_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _competitor_summary(competitors: list[CompetitorData]) -> dict[str, object]:
    if not competitors:
        return {"count": 0}
    prices = [c.price for c in competitors if c.price is not None]
    ratings = [c.rating for c in competitors if c.rating is not None]
    reviews = [c.review_count for c in competitors if c.review_count is not None]
    summary: dict[str, object] = {"count": len(competitors)}
    if prices:
        summary["avg_price"] = round(sum(prices) / len(prices), 2)
        summary["min_price"] = min(prices)
        summary["max_price"] = max(prices)
    if ratings:
        summary["avg_rating"] = round(sum(ratings) / len(ratings), 2)
    if reviews:
        summary["avg_review_count"] = round(sum(reviews) / len(reviews))
    return summary


async def _generate_report(
    state: TaskState,
    scoring_result: SelectionResult,
    competitor_summary: dict[str, object],
) -> str:
    product_info = state.get("product_info") or {}
    prompt = (
        "You are an e-commerce selection analyst.\n"
        f"SKU: {state['sku']}\n"
        f"Platform: {state.get('platform', 'amazon')}\n"
        f"Marketplace: {state.get('market', 'US')}\n"
        f"Category: {product_info.get('category', 'N/A')}\n"
        f"Price: {product_info.get('price', 'N/A')}\n"
        f"Competitor summary: {json.dumps(competitor_summary)}\n"
        f"Scoring: total={scoring_result.total_score:.1f}, "
        f"demand={scoring_result.demand_score:.1f}, "
        f"competition={scoring_result.competition_score:.1f}, "
        f"profitability={scoring_result.profitability_score:.1f}, "
        f"completeness={scoring_result.completeness_score:.1f}\n"
        f"Recommendation: {scoring_result.recommendation}\n\n"
        "Write a concise selection analysis report (3-5 sentences) covering: "
        "market demand signal, competitive landscape, profitability outlook, "
        "and final recommendation."
    )
    provider = get_llm_provider()
    response = await provider.chat(
        [
            Message(role="system", content="You write concise e-commerce analysis reports."),
            Message(role="user", content=prompt),
        ],
        temperature=0.3,
    )
    return response.content.strip()


async def selection_node(state: TaskState) -> dict[str, object]:
    """selection_agent — score product + generate analysis report."""
    trace = [with_started_trace(state, "selection_agent")]
    product_info = state.get("product_info") or {}
    competitors = _extract_competitors(product_info)
    selection_input = _build_selection_input(state, competitors)
    scoring_result = score_product(selection_input)
    competitor_summary = _competitor_summary(competitors)

    try:
        report = await _generate_report(state, scoring_result, competitor_summary)
    except Exception as exc:
        report = (
            f"Selection analysis for {state['sku']}: "
            f"score={scoring_result.total_score:.1f}/100, "
            f"recommendation={scoring_result.recommendation}. "
            f"Competitors: {len(competitors)}. "
            f"(LLM report generation failed: {exc})"
        )
        trace.append(
            make_trace_event(
                "selection_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc), "fallback": "scoring_only"},
            )
        )

    trace.append(
        make_trace_event(
            "selection_agent",
            AgentTraceStatus.COMPLETED,
            detail={
                "total_score": round(scoring_result.total_score, 2),
                "recommendation": scoring_result.recommendation,
                "competitor_count": len(competitors),
                "report_generated": True,
            },
        )
    )

    return {
        "selection": {
            **scoring_result.to_dict(),
            "competitor_summary": competitor_summary,
            "report": report,
        },
        "trace": trace,
    }
