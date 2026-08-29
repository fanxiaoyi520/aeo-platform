from typing import Any

from aeo_shared.responses import success_response
from fastapi import APIRouter, Request

from aeo_api.db.models import check_database
from aeo_api.db.redis import check_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Liveness probe — P-API-04."""
    return success_response({"status": "ok"}, request.state.request_id).model_dump()


@router.get("/ready")
async def ready(request: Request) -> dict[str, Any]:
    """Readiness probe — checks DB and Redis."""
    db_ok = await check_database()
    redis_ok = await check_redis()
    status = "ready" if db_ok and redis_ok else "not_ready"
    return success_response(
        {"status": status, "database": db_ok, "redis": redis_ok},
        request.state.request_id,
    ).model_dump()
