"""Support scripts API — MV4-03: after-sales script library."""

from __future__ import annotations

from typing import Any

from aeo_shared.after_sales_scripts import get_script_library
from aeo_shared.responses import success_response
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/support", tags=["support"])


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


@router.get("/scripts")
async def list_support_scripts(
    request: Request,
    scenario: str | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Return after-sales scripts with optional filtering."""
    lib = get_script_library()
    scripts = lib.filter_by(scenario=scenario, platform=platform)
    payload = {
        "scripts": [s.to_dict() for s in scripts],
        "summary": {
            "total": len(scripts),
            "scenarios": lib.list_scenarios(),
            "platforms": lib.list_platforms(),
        },
    }
    return _ok(request, payload)
