"""P5-04: Dual-mode auth middleware — JWT + legacy API key."""

from __future__ import annotations

import structlog
from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from jwt import PyJWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from aeo_api.auth.context import current_tenant_id, current_user_id, current_user_role
from aeo_api.auth.jwt_service import decode_token
from aeo_api.db.tenant_models import SYSTEM_TENANT_ID
from aeo_api.middleware.paths import is_public_path

logger = structlog.get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authenticate via JWT (preferred) or API key (backward-compatible).

    JWT path: decode token → set tenant_id / user_id / role on request.state + contextvars.
    API key path: match against configured key → system tenant, role=owner.
    Neither matches → 401.
    """

    def __init__(self, app: ASGIApp, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if is_public_path(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()

        if not token:
            return self._unauthorized(request)

        jwt_payload = self._try_jwt(token)
        if jwt_payload is not None:
            request.state.tenant_id = str(jwt_payload.tid)
            request.state.user_id = str(jwt_payload.sub)
            request.state.user_role = jwt_payload.role
        elif token == self._api_key:
            request.state.tenant_id = SYSTEM_TENANT_ID
            request.state.user_id = "system"
            request.state.user_role = "owner"
        else:
            return self._unauthorized(request)

        ctx_tenant = current_tenant_id.set(request.state.tenant_id)
        ctx_user = current_user_id.set(request.state.user_id)
        ctx_role = current_user_role.set(request.state.user_role)
        structlog.contextvars.bind_contextvars(
            tenant_id=request.state.tenant_id,
            user_id=request.state.user_id,
        )
        try:
            return await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("tenant_id", "user_id")
            current_tenant_id.reset(ctx_tenant)
            current_user_id.reset(ctx_user)
            current_user_role.reset(ctx_role)

    @staticmethod
    def _try_jwt(token: str):
        try:
            payload = decode_token(token)
            if payload.type != "access":
                return None
            return payload
        except PyJWTError:
            return None

    @staticmethod
    def _unauthorized(request: Request) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        body = error_response(ErrorCode.UNAUTHORIZED, request_id)
        return JSONResponse(status_code=401, content=body.model_dump())
