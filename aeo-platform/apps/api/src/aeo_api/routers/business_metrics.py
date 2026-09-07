"""Business metrics dashboard API — MV4-06."""

from __future__ import annotations

from typing import Any

from aeo_shared.dashboard import DashboardService, _generate_mock_snapshots
from aeo_shared.responses import success_response
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/business-metrics", tags=["business-metrics"])


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


@router.get("/dashboard")
async def get_business_dashboard(request: Request) -> dict[str, Any]:
    """Return aggregated GMV/ROI/automation-rate dashboard."""
    snapshots = _generate_mock_snapshots(days=30)
    service = DashboardService()
    dashboard = service.build(
        snapshots=snapshots,
        auto_completed=135,
        total=300,
    )
    return _ok(request, dashboard)
