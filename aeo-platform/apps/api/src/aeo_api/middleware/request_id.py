import uuid

import structlog
from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from aeo_api.middleware.paths import is_public_path

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

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if is_public_path(request.url.path):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        if token != self._api_key:
            request_id = getattr(request.state, "request_id", "")
            body = error_response(ErrorCode.UNAUTHORIZED, request_id)
            return JSONResponse(status_code=401, content=body.model_dump())

        return await call_next(request)
