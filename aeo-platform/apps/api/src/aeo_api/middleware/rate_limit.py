import hashlib
import time

import structlog
from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from aeo_api.db.redis import get_redis
from aeo_api.middleware.paths import is_public_path

logger = structlog.get_logger(__name__)


def _rate_limit_key(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    user_id = getattr(request.state, "user_id", None)
    if tenant_id and user_id:
        raw = f"{tenant_id}:{user_id}"
    else:
        raw = request.client.host if request.client else "unknown"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    minute_bucket = int(time.time()) // 60
    return f"ratelimit:{digest}:{minute_bucket}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed fixed-window rate limit per API key (default 100 req/min)."""

    def __init__(self, app: ASGIApp, limit_per_minute: int) -> None:
        super().__init__(app)
        self._limit = limit_per_minute

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if is_public_path(request.url.path):
            return await call_next(request)

        redis_key = _rate_limit_key(request)
        try:
            redis = await get_redis()
            count = await redis.incr(redis_key)
            if count == 1:
                await redis.expire(redis_key, 60)
            if count > self._limit:
                request_id = getattr(request.state, "request_id", "")
                logger.warning("rate limit exceeded", path=request.url.path, count=count)
                body = error_response(ErrorCode.RATE_LIMITED, request_id)
                return JSONResponse(
                    status_code=429,
                    content=body.model_dump(),
                    headers={"Retry-After": "60"},
                )
        except Exception:
            logger.exception("rate limit check failed; allowing request")

        return await call_next(request)
