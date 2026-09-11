"""P5-03: Auth API router — signup, login, refresh, me."""

from typing import Annotated, Any

from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response, success_response
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.auth.auth_service import AuthError, login, refresh_tokens, signup
from aeo_api.auth.rbac import CurrentRole, CurrentTenant, CurrentUser
from aeo_api.db.models import get_db_session
from aeo_api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


def _user_response(user: object) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        tenant_id=str(user.tenant_id),
    )


@router.post("/signup")
async def signup_endpoint(
    request: Request, body: SignupRequest, session: DbSession
) -> dict[str, Any]:
    try:
        user, _tenant = await signup(
            session,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            tenant_name=body.tenant_name,
            tenant_slug=body.tenant_slug,
        )
    except AuthError as exc:
        err = error_response(ErrorCode.TENANT_ALREADY_EXISTS, request.state.request_id, exc.message)
        return JSONResponse(status_code=409, content=err.model_dump())

    from aeo_api.auth.jwt_service import create_access_token, create_refresh_token

    access_token = create_access_token(user.id, user.tenant_id, user.role)
    refresh_token = create_refresh_token(user.id, user.tenant_id)
    token_data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_response(user),
    )
    return _ok(request, token_data.model_dump())


@router.post("/login")
async def login_endpoint(
    request: Request, body: LoginRequest, session: DbSession
) -> dict[str, Any]:
    try:
        user, access_token, refresh_token = await login(session, body.email, body.password)
    except AuthError:
        err = error_response(ErrorCode.AUTH_INVALID_CREDENTIALS, request.state.request_id)
        return JSONResponse(status_code=401, content=err.model_dump())

    token_data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_response(user),
    )
    return _ok(request, token_data.model_dump())


@router.post("/refresh")
async def refresh_endpoint(
    request: Request, body: RefreshRequest, session: DbSession
) -> dict[str, Any]:
    try:
        new_access, new_refresh = await refresh_tokens(session, body.refresh_token)
    except AuthError:
        err = error_response(ErrorCode.AUTH_TOKEN_EXPIRED, request.state.request_id)
        return JSONResponse(status_code=401, content=err.model_dump())

    return _ok(
        request,
        {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"},
    )


@router.post("/me")
async def me_endpoint(
    request: Request,
    user_id: CurrentUser,
    tenant_id: CurrentTenant,
    role: CurrentRole,
) -> dict[str, Any]:
    return _ok(
        request,
        {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role,
        },
    )
