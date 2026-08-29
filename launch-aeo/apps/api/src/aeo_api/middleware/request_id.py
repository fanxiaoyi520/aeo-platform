import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            structlog.contextvars.unbind_contextvars("request_id")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Simple API key auth — skipped for health endpoints."""

    def __init__(self, app: ASGIApp, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key
        self._public_paths = {
            "/",
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/docs/oauth2-redirect",
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self._public_paths:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        if token != self._api_key:
            from aeo_shared.errors import ErrorCode
            from aeo_shared.responses import error_response
            from fastapi.responses import JSONResponse

            request_id = getattr(request.state, "request_id", "")
            body = error_response(ErrorCode.UNAUTHORIZED, request_id)
            return JSONResponse(status_code=401, content=body.model_dump())

        return await call_next(request)
