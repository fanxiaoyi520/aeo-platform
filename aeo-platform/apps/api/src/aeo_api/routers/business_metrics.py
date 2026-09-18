"""Business metrics dashboard API — MV4-06 / P6-29 live aggregation."""

from __future__ import annotations

from typing import Annotated, Any

from aeo_shared.dashboard import DashboardService, _generate_mock_snapshots
from aeo_shared.responses import success_response
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import get_db_session
from aeo_api.services.metrics_aggregation import MetricsAggregationService, has_live_data

router = APIRouter(prefix="/api/v1/business-metrics", tags=["business-metrics"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


@router.get("/dashboard")
async def get_business_dashboard(
    request: Request,
    db: DbSession,
) -> dict[str, Any]:
    """Return aggregated GMV/ROI/automation-rate dashboard.

    Uses live data from DB when available, falls back to mock otherwise.
    """
    snapshots: list[Any] | None = None
    try:
        service = MetricsAggregationService(db)
        snapshots = await service.build_live_snapshots(days=30)
    except Exception:
        snapshots = None

    data_source = "live" if snapshots and has_live_data(snapshots) else "mock"
    if not snapshots:
        snapshots = _generate_mock_snapshots(days=30)

    dashboard_service = DashboardService()
    dashboard = dashboard_service.build(
        snapshots=snapshots,
        auto_completed=135,
        total=300,
    )
    dashboard["data_source"] = data_source
    return _ok(request, dashboard)
