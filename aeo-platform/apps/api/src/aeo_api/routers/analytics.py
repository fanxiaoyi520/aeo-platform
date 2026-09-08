"""Analytics report API — MV4-04/05: daily/weekly business review + strategy task creation."""

from __future__ import annotations

from datetime import date
from typing import Any

from aeo_shared.agent_catalog import get_default_registry
from aeo_shared.metrics_sdk import BusinessMetricsSnapshot
from aeo_shared.responses import success_response
from aeo_shared.strategy_task_creator import StrategyTaskCreator, get_action_mapping
from aeo_shared.task_scheduler import AgentTaskScheduler
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


class SuggestionInput(BaseModel):
    action: str
    sku: str = ""
    reason: str = ""


class CreateTasksRequest(BaseModel):
    suggestions: list[SuggestionInput] = Field(default_factory=list)
    parent_task_id: str | None = None


def _build_mock_report() -> dict[str, Any]:
    today = date.today()
    snapshots = []
    for i in range(7):
        from datetime import timedelta
        from decimal import Decimal

        day = today - timedelta(days=i)
        gmv = Decimal(str(800 + (i * 50)))
        ad_spend = Decimal(str(200 + (i * 10)))
        roi = (gmv / ad_spend).quantize(Decimal("0.01")) if ad_spend > 0 else None
        snapshots.append(
            BusinessMetricsSnapshot(
                snapshot_date=day,
                platform="amazon",
                marketplace="US",
                gmv=gmv,
                ad_spend=ad_spend,
                roi=roi,
                order_count=20 + i * 3,
                unique_skus=5 + i,
                data_source="mock",
            )
        )

    total_gmv = sum(s.gmv for s in snapshots)
    total_ad_spend = sum(s.ad_spend for s in snapshots)
    total_orders = sum(s.order_count for s in snapshots)

    return {
        "generated_at": today.isoformat(),
        "report": "Business review report (mock data)",
        "metrics_summary": {
            "total_gmv": str(total_gmv),
            "total_ad_spend": str(total_ad_spend),
            "total_orders": total_orders,
            "period_days": 7,
        },
    }


@router.get("/report")
async def get_analytics_report(request: Request) -> dict[str, Any]:
    """Return a business review report with metrics summary."""
    report = _build_mock_report()
    return _ok(request, report)


@router.post("/create_tasks")
async def create_tasks_from_strategy(
    request: Request,
    body: CreateTasksRequest,
) -> dict[str, Any]:
    """Create follow-up tasks from strategy suggestions."""
    registry = get_default_registry()
    scheduler = AgentTaskScheduler(registry)
    creator = StrategyTaskCreator(scheduler=scheduler, mapping=get_action_mapping())

    suggestions = [s.model_dump() for s in body.suggestions]
    created = creator.create_tasks(suggestions, parent_task_id=body.parent_task_id)
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
    return _ok(request, {"created_tasks": created_tasks})
