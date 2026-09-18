"""P7-01: Performance monitoring middleware."""

from __future__ import annotations

import time

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

SLOW_REQUEST_THRESHOLD_MS = 500


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Monitor request performance and log slow requests."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}"

        if process_time_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "slow_request",
                method=request.method,
                url=str(request.url),
                process_time_ms=round(process_time_ms, 2),
                status_code=response.status_code,
            )
        else:
            logger.info(
                "request_completed",
                method=request.method,
                url=str(request.url),
                process_time_ms=round(process_time_ms, 2),
                status_code=response.status_code,
            )

        return response
