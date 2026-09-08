"""MV3-08: Recommendations API — ads/ops/linkage suggestions + approval workflow."""

from __future__ import annotations

from typing import Any, Literal, cast

from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response, success_response
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from aeo_api.schemas.recommendations import AdsResponse, LinkageResponse, OpsResponse

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])

_PlatformChoice = Literal["amazon", "tiktok"]


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


def _error(request: Request, code: ErrorCode, status: int, detail: str = "") -> JSONResponse:
    body = error_response(code, request.state.request_id, detail).model_dump()
    return JSONResponse(status_code=status, content=body)


@router.get("/ads", response_model=None)
async def get_ads_recommendations(
    request: Request,
    sku: str = "PILOT-001",
    platform: str = "amazon",
    market: str = "US",
) -> dict[str, Any] | JSONResponse:
    try:
        from aeo_orchestrator.runner import run_ads_task

        result = await run_ads_task(
            sku=sku,
            platform=cast(_PlatformChoice, platform),
            market=market,
            task_id=f"rec-ads-{sku}",
        )
        payload: dict[str, Any] = {
            "task_id": result.get("task_id", ""),
            "sku": result.get("sku", sku),
            "platform": result.get("platform", platform),
            "market": result.get("market", market),
            "ads": result.get("ads") or {},
            "trace": result.get("trace") or [],
        }
        return _ok(request, AdsResponse(**payload).model_dump())
    except Exception as exc:
        return _error(request, ErrorCode.INTERNAL_ERROR, 500, str(exc))


@router.get("/ops", response_model=None)
async def get_ops_recommendations(
    request: Request,
    sku: str = "PILOT-001",
    platform: str = "amazon",
    market: str = "US",
) -> dict[str, Any] | JSONResponse:
    try:
        from aeo_orchestrator.runner import run_ops_task

        result = await run_ops_task(
            sku=sku,
            platform=cast(_PlatformChoice, platform),
            market=market,
            task_id=f"rec-ops-{sku}",
        )
        payload: dict[str, Any] = {
            "task_id": result.get("task_id", ""),
            "sku": result.get("sku", sku),
            "platform": result.get("platform", platform),
            "market": result.get("market", market),
            "ops": result.get("ops") or {},
            "trace": result.get("trace") or [],
        }
        return _ok(request, OpsResponse(**payload).model_dump())
    except Exception as exc:
        return _error(request, ErrorCode.INTERNAL_ERROR, 500, str(exc))


@router.get("/linkage", response_model=None)
async def get_linkage_recommendations(request: Request) -> dict[str, Any] | JSONResponse:
    try:
        recs = _fetch_linkage_recommendations()
        return _ok(
            request,
            LinkageResponse(
                recommendations=[r.model_dump() for r in recs],
            ).model_dump(),
        )
    except Exception as exc:
        return _error(request, ErrorCode.INTERNAL_ERROR, 500, str(exc))


def _fetch_linkage_recommendations() -> list[Any]:
    from aeo_integrations.amazon.advertising import get_advertising_client
    from aeo_integrations.amazon.inventory import get_inventory_client
    from aeo_shared.ads_inventory_linkage import AdsInventoryLinkage

    ads_client = get_advertising_client()
    inv_client = get_inventory_client()

    campaigns = [c.model_dump() for c in ads_client.list_campaigns()]
    snapshots = [s.model_dump() for s in ads_client.list_spend_snapshots()]
    inventory = [i.model_dump() for i in inv_client.list_inventory()]

    for camp in campaigns:
        camp.setdefault("sku", f"SKU-{camp['campaign_id']}")

    linkage = AdsInventoryLinkage()
    return linkage.analyze(campaigns, snapshots, inventory)
