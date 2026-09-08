"""ads_agent — MV3-02 campaign analysis + bid suggestions + ROI simulation."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from aeo_integrations.amazon.advertising import get_advertising_client
from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


def _to_float(value: Decimal | str | int | float | None) -> float:
    if value is None:
        return 0.0
    return float(str(value))


def calculate_campaign_metrics(
    campaigns: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    total_spend = sum(_to_float(s.get("spend")) for s in snapshots)
    total_gmv = sum(_to_float(s.get("attributed_gmv")) for s in snapshots)
    total_impressions = sum(int(s.get("impressions", 0)) for s in snapshots)
    total_clicks = sum(int(s.get("clicks", 0)) for s in snapshots)

    avg_acos = (total_spend / total_gmv * 100) if total_gmv > 0 else 0.0
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0

    return {
        "total_spend": round(total_spend, 2),
        "total_gmv": round(total_gmv, 2),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "avg_acos": round(avg_acos, 2),
        "avg_ctr": round(avg_ctr, 2),
        "campaign_count": len(campaigns),
    }


def _build_campaign_summary(
    campaigns: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_campaign: dict[str, list[dict[str, Any]]] = {}
    for snap in snapshots:
        cid = str(snap.get("campaign_id", ""))
        by_campaign.setdefault(cid, []).append(snap)

    summaries = []
    for camp in campaigns:
        cid = str(camp.get("campaign_id", ""))
        camp_snaps = by_campaign.get(cid, [])
        spend = sum(_to_float(s.get("spend")) for s in camp_snaps)
        gmv = sum(_to_float(s.get("attributed_gmv")) for s in camp_snaps)
        impressions = sum(int(s.get("impressions", 0)) for s in camp_snaps)
        clicks = sum(int(s.get("clicks", 0)) for s in camp_snaps)
        acos = (spend / gmv * 100) if gmv > 0 else None
        ctr = (clicks / impressions * 100) if impressions > 0 else None

        summaries.append(
            {
                "campaign_id": cid,
                "name": camp.get("name", ""),
                "status": camp.get("status", ""),
                "campaign_type": camp.get("campaign_type", ""),
                "daily_budget": str(camp.get("daily_budget", "")),
                "total_spend": round(spend, 2),
                "total_gmv": round(gmv, 2),
                "acos": round(acos, 2) if acos is not None else None,
                "ctr": round(ctr, 2) if ctr is not None else None,
                "impressions": impressions,
                "clicks": clicks,
            }
        )
    return summaries


def _build_user_prompt(
    state: TaskState,
    campaign_summaries: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> str:
    sku = state.get("sku", "")
    product_info = state.get("product_info") or {}

    return (
        f"You are an Amazon advertising specialist.\n"
        f"SKU: {sku}\n"
        f"Product: {product_info.get('title', 'N/A')}\n"
        f"Price: {product_info.get('price', 'N/A')}\n\n"
        f"Portfolio metrics:\n{json.dumps(metrics, indent=2)}\n\n"
        f"Campaign details:\n{json.dumps(campaign_summaries, indent=2)}\n\n"
        "Provide campaign optimization suggestions in JSON format:\n"
        '{"suggestions": [{"campaign_id": "...", '
        '"type": "bid_increase|bid_decrease|pause|budget_increase", '
        '"reason": "...", "suggested_value": "..."}], '
        '"bid_simulation": {"campaign_id": "...", "current_bid": "...", '
        '"suggested_bid": "...", '
        '"estimated_impression_lift": "...", "estimated_gmv_change": "..."}, '
        '"report": "concise narrative summary (3-5 sentences)"}'
    )


def _parse_llm_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        return {"suggestions": [], "bid_simulation": None, "report": text}


async def ads_node(state: TaskState) -> dict[str, object]:
    """ads_agent — analyze campaigns + generate bid/structure suggestions."""
    trace = [with_started_trace(state, "ads_agent")]

    try:
        ad_client = get_advertising_client()
        campaigns = ad_client.list_campaigns()
        snapshots = ad_client.list_spend_snapshots()

        campaign_dicts = [c.model_dump() for c in campaigns]
        snapshot_dicts = [s.model_dump() for s in snapshots]

        metrics = calculate_campaign_metrics(campaign_dicts, snapshot_dicts)
        campaign_summaries = _build_campaign_summary(campaign_dicts, snapshot_dicts)

        prompt = _build_user_prompt(state, campaign_summaries, metrics)
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(
                    role="system",
                    content=(
                        "You are an Amazon advertising optimization specialist. "
                        "Analyze campaign performance and provide actionable suggestions "
                        "for bid adjustments, budget changes, and campaign structure. "
                        "Output valid JSON only."
                    ),
                ),
                Message(role="user", content=prompt),
            ],
            temperature=0.3,
        )

        parsed = _parse_llm_json(response.content)

        result = {
            "campaigns": campaign_summaries,
            "metrics": metrics,
            "suggestions": parsed.get("suggestions", []),
            "bid_simulation": parsed.get("bid_simulation"),
            "report": parsed.get("report", ""),
        }

        trace.append(
            make_trace_event(
                "ads_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "campaign_count": len(campaigns),
                    "suggestion_count": len(result["suggestions"]),
                    "total_spend": metrics["total_spend"],
                    "total_gmv": metrics["total_gmv"],
                },
            )
        )

    except Exception as exc:
        result = {
            "campaigns": [],
            "metrics": {},
            "suggestions": [],
            "bid_simulation": None,
            "report": f"Ads analysis failed: {exc}",
            "error": str(exc),
        }
        trace.append(
            make_trace_event(
                "ads_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"ads": result, "trace": trace}
