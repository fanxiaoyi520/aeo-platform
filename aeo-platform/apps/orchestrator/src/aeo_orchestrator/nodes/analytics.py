"""analytics_agent — MV4-04 daily/weekly report generation + strategy suggestions."""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message
from aeo_shared.agent_catalog import get_default_registry
from aeo_shared.metrics_sdk import (
    AdSpendMetricRecord,
    BusinessMetricsSnapshot,
    OrderMetricRecord,
    build_daily_snapshot,
)
from aeo_shared.strategy_task_creator import StrategyTaskCreator, get_action_mapping
from aeo_shared.task_scheduler import AgentTaskScheduler

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


async def _fetch_live_metrics_from_db(
    *,
    platform: str,
    marketplace: str,
    days: int = 7,
) -> list[BusinessMetricsSnapshot] | None:
    """Fetch live metrics from DB using psycopg. Returns None if DB unavailable."""
    try:
        import psycopg

        db_url = os.environ.get("DB_URL_SYNC") or os.environ.get("DB_URL")
        if not db_url:
            return None

        today = date.today()
        start_date = today - timedelta(days=days - 1)
        start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)

        orders: list[OrderMetricRecord] = []
        ad_spends: list[AdSpendMetricRecord] = []

        with psycopg.connect(db_url) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT sku, quantity, item_price, platform, marketplace,
                       purchase_date, data_source
                FROM order_records
                WHERE platform = %s AND marketplace = %s AND purchase_date >= %s
                """,
                (platform, marketplace, start_dt),
            )
            for row in cur.fetchall():
                orders.append(
                    OrderMetricRecord(
                        sku=row[0],
                        quantity=row[1],
                        item_price=row[2],
                        platform=row[3],
                        marketplace=row[4],
                        purchase_date=row[5],
                        data_source=row[6],
                    )
                )

            cur.execute(
                """
                SELECT s.spend, s.attributed_gmv, s.snapshot_date, %s as platform,
                       s.data_source
                FROM ad_spend_snapshots s
                JOIN ad_campaigns c ON s.campaign_id = c.id
                WHERE c.platform = %s AND s.snapshot_date >= %s
                """,
                (platform, platform, start_dt),
            )
            for row in cur.fetchall():
                ad_spends.append(
                    AdSpendMetricRecord(
                        spend=row[0],
                        attributed_gmv=row[1],
                        snapshot_date=row[2],
                        platform=row[3],
                        data_source=row[4],
                    )
                )

        if not orders and not ad_spends:
            return None

        snapshots = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            snapshot = build_daily_snapshot(
                orders=orders,
                ad_spends=ad_spends,
                snapshot_date=day,
                platform=platform,
                marketplace=marketplace,
            )
            snapshots.append(
                BusinessMetricsSnapshot(
                    snapshot_date=snapshot.snapshot_date,
                    platform=snapshot.platform,
                    marketplace=snapshot.marketplace,
                    gmv=snapshot.gmv,
                    ad_spend=snapshot.ad_spend,
                    roi=snapshot.roi,
                    order_count=snapshot.order_count,
                    unique_skus=snapshot.unique_skus,
                    automation_rate=snapshot.automation_rate,
                    data_source="live",
                )
            )

        return snapshots
    except Exception:
        return None


def _generate_mock_metrics(
    *,
    platform: str,
    marketplace: str,
    days: int = 7,
) -> list[BusinessMetricsSnapshot]:
    """Fallback mock metrics when live data is unavailable."""
    today = date.today()
    snapshots = []
    for i in range(days):
        day = today - timedelta(days=i)
        gmv = Decimal(str(800 + (i * 50)))
        ad_spend = Decimal(str(200 + (i * 10)))
        roi = (gmv / ad_spend).quantize(Decimal("0.01")) if ad_spend > 0 else None
        snapshots.append(
            BusinessMetricsSnapshot(
                snapshot_date=day,
                platform=platform,
                marketplace=marketplace,
                gmv=gmv,
                ad_spend=ad_spend,
                roi=roi,
                order_count=20 + i * 3,
                unique_skus=5 + i,
                data_source="mock",
            )
        )
    return snapshots


def _build_metrics_summary(snapshots: list[BusinessMetricsSnapshot]) -> dict[str, Any]:
    if not snapshots:
        return {"total_gmv": "0", "total_ad_spend": "0", "total_orders": 0, "avg_roi": None}

    total_gmv = sum(s.gmv for s in snapshots)
    total_ad_spend = sum(s.ad_spend for s in snapshots)
    total_orders = sum(s.order_count for s in snapshots)
    rois = [s.roi for s in snapshots if s.roi is not None]
    avg_roi: Decimal | None = Decimal(str(sum(rois) / len(rois))) if rois else None

    return {
        "total_gmv": str(total_gmv),
        "total_ad_spend": str(total_ad_spend),
        "total_orders": total_orders,
        "avg_roi": str(avg_roi.quantize(Decimal("0.01"))) if avg_roi else None,
        "period_days": len(snapshots),
        "daily_snapshots": [s.to_dict() for s in snapshots],
    }


def _build_user_prompt(
    state: TaskState,
    metrics_summary: dict[str, Any],
) -> str:
    sku = state.get("sku", "")
    product_info = state.get("product_info") or {}

    return (
        f"You are a business analytics specialist.\n"
        f"Primary SKU: {sku}\n"
        f"Product: {product_info.get('title', 'N/A')}\n\n"
        f"Metrics summary (last 7 days):\n{json.dumps(metrics_summary, indent=2)}\n\n"
        "Generate a business review report in JSON format:\n"
        '{"daily_summary": "narrative summary of today\'s performance", '
        '"weekly_trend": "narrative of 7-day trend with key changes", '
        '"strategy_suggestions": [{"action": "action_type", "sku": "...", "reason": "..."}], '
        '"kpi_targets": {"daily_gmv_target": 1000, '
        '"daily_gmv_actual": ..., "target_met": true/false}}'
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
            "daily_summary": text,
            "weekly_trend": "",
            "strategy_suggestions": [],
            "kpi_targets": {},
        }


async def analytics_node(state: TaskState) -> dict[str, object]:
    """analytics_agent — generate daily/weekly business review reports with strategy suggestions."""
    trace = [with_started_trace(state, "analytics_agent")]

    try:
        platform = state.get("platform", "amazon")
        market = state.get("market", "US")

        snapshots = await _fetch_live_metrics_from_db(platform=platform, marketplace=market, days=7)
        data_source = "live"
        if not snapshots or not any(s.gmv > 0 or s.order_count > 0 for s in snapshots):
            snapshots = _generate_mock_metrics(platform=platform, marketplace=market, days=7)
            data_source = "mock"

        metrics_summary = _build_metrics_summary(snapshots)
        metrics_summary["data_source"] = data_source

        dtc_kpis: dict[str, Any] = {}
        if platform == "shopify":
            from aeo_shared.dtc_analytics import (
                build_dtc_metrics_prompt_section,
                calculate_dtc_kpis,
            )

            try:
                from aeo_integrations.shopify.store import get_store_client

                store = get_store_client()
                store_metrics = [m.model_dump() for m in store.get_store_metrics(limit=7)]
                customers = [c.model_dump() for c in store.list_customers()]
                carts = [c.model_dump() for c in store.list_abandoned_carts()]
                dtc_kpis = calculate_dtc_kpis(store_metrics, customers, carts)
            except Exception:
                dtc_kpis = {}

        prompt = _build_user_prompt(state, metrics_summary)
        if dtc_kpis:
            from aeo_shared.dtc_analytics import build_dtc_metrics_prompt_section

            prompt += build_dtc_metrics_prompt_section(dtc_kpis)
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(
                    role="system",
                    content=(
                        "You are a business analytics specialist. "
                        "Analyze the provided metrics data and generate "
                        "a concise business review report. "
                        "Include daily summary, weekly trend, "
                        "strategy suggestions, and KPI target tracking. "
                        "Output valid JSON only."
                    ),
                ),
                Message(role="user", content=prompt),
            ],
            temperature=0.3,
        )

        parsed = _parse_llm_json(response.content)

        daily_summary = parsed.get("daily_summary", "")
        weekly_trend = parsed.get("weekly_trend", "")
        strategy_suggestions = parsed.get("strategy_suggestions", [])
        kpi_targets = parsed.get("kpi_targets", {})

        report_lines = [
            "# Business Review Report",
            "",
            f"**Platform:** {platform} | **Market:** {market}",
            f"**Period:** Last {len(snapshots)} days",
            "",
            "## Daily Summary",
            daily_summary,
            "",
            "## Weekly Trend",
            weekly_trend,
            "",
            "## Metrics Overview",
            f"- Total GMV: ${metrics_summary['total_gmv']}",
            f"- Total Ad Spend: ${metrics_summary['total_ad_spend']}",
            f"- Total Orders: {metrics_summary['total_orders']}",
            f"- Avg ROI: {metrics_summary['avg_roi'] or 'N/A'}",
        ]
        if strategy_suggestions:
            report_lines.extend(["", "## Strategy Suggestions"])
            for i, s in enumerate(strategy_suggestions, 1):
                report_lines.append(f"{i}. **{s.get('action', 'N/A')}** — {s.get('reason', '')}")
        report = "\n".join(report_lines)

        registry = get_default_registry()
        scheduler = AgentTaskScheduler(registry)
        creator = StrategyTaskCreator(scheduler=scheduler, mapping=get_action_mapping())
        task_id = state.get("task_id")
        created = creator.create_tasks(strategy_suggestions, parent_task_id=task_id)
        created_tasks = [
            {
                "task_id": t.task_id,
                "agent_id": t.agent_id,
                "capability": t.capability,
                "priority": t.priority.value,
                "payload": t.payload,
                "parent_task_id": t.parent_task_id,
            }
            for t in created
        ]

        result = {
            "daily_summary": daily_summary,
            "weekly_trend": weekly_trend,
            "strategy_suggestions": strategy_suggestions,
            "kpi_targets": kpi_targets,
            "metrics_summary": metrics_summary,
            "dtc_kpis": dtc_kpis,
            "report": report,
            "created_tasks": created_tasks,
        }

        trace.append(
            make_trace_event(
                "analytics_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "period_days": len(snapshots),
                    "total_gmv": metrics_summary["total_gmv"],
                    "total_orders": metrics_summary["total_orders"],
                    "strategy_count": len(strategy_suggestions),
                },
            )
        )

    except Exception as exc:
        result = {
            "daily_summary": "",
            "weekly_trend": "",
            "strategy_suggestions": [],
            "kpi_targets": {},
            "metrics_summary": {},
            "dtc_kpis": {},
            "report": f"Analytics report generation failed: {exc}",
            "error": str(exc),
            "created_tasks": [],
        }
        trace.append(
            make_trace_event(
                "analytics_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"analytics": result, "trace": trace}
