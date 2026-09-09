"""Middleware to record Prometheus metrics for HTTP requests."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from aeo_api.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request count, duration, and in-progress gauge for every HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        method = request.method
        endpoint = self._normalize_path(request.url.path)

        HTTP_REQUESTS_IN_PROGRESS.inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
            HTTP_REQUESTS_IN_PROGRESS.dec()

    @staticmethod
    def _normalize_path(path: str) -> str:
        parts = path.strip("/").split("/")
        if len(parts) < 4 or parts[0] != "api" or parts[1] != "v1":
            return path
        normalized = []
        for i, part in enumerate(parts):
            if i >= 3 and part and not part.startswith("{"):
                clean = part.replace("-", "").replace("_", "")
                has_digits = any(c.isdigit() for c in part)
                has_alpha = any(c.isalpha() for c in part)
                is_id = (has_digits and has_alpha) or len(part) > 20
                if clean.isalnum() and is_id:
                    normalized.append(":id")
                else:
                    normalized.append(part)
            else:
                normalized.append(part)
        return "/" + "/".join(normalized)
