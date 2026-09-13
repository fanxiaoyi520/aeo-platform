"""P5-07: Tenant admin API router."""

from typing import Annotated, Any
from uuid import UUID

from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response, success_response
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.auth.rbac import CurrentRole, CurrentTenant, CurrentUser
from aeo_api.auth.tenant_service import (
    TenantServiceError,
    deactivate_member,
    get_tenant,
    invite_member,
    list_members,
    update_member_role,
    update_tenant,
)
from aeo_api.db.models import get_db_session
from aeo_api.schemas.tenant import (
    InviteMemberRequest,
    TenantMemberResponse,
    TenantResponse,
    TenantUpdateRequest,
    UpdateMemberRoleRequest,
)

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _ok(request: Request, data: Any) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


def _tenant_response(tenant: Any) -> TenantResponse:
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan,
        is_active=tenant.is_active,
        settings=tenant.settings,
        created_at=tenant.created_at.isoformat(),
        updated_at=tenant.updated_at.isoformat(),
    )


def _member_response(user: Any) -> TenantMemberResponse:
    return TenantMemberResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat(),
    )


def _require_owner_or_admin(role: str) -> None:
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Owner or admin role required")


def _require_owner(role: str) -> None:
    if role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")


@router.get("/me")
async def get_current_tenant(
    request: Request,
    tenant_id: CurrentTenant,
    session: DbSession,
) -> dict[str, Any]:
    tenant = await get_tenant(session, UUID(tenant_id))
    return _ok(request, _tenant_response(tenant).model_dump())


@router.patch("/me")
async def update_current_tenant(
    request: Request,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    body: TenantUpdateRequest,
    session: DbSession,
) -> dict[str, Any]:
    _require_owner_or_admin(role)
    tenant = await update_tenant(session, UUID(tenant_id), name=body.name, settings=body.settings)
    return _ok(request, _tenant_response(tenant).model_dump())


@router.get("/me/users")
async def list_tenant_members(
    request: Request,
    tenant_id: CurrentTenant,
    session: DbSession,
) -> dict[str, Any]:
    members = await list_members(session, UUID(tenant_id))
    items = [_member_response(m).model_dump() for m in members]
    return _ok(request, {"items": items, "total": len(items)})


@router.post("/me/users", response_model=None)
async def invite_tenant_member(
    request: Request,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    body: InviteMemberRequest,
    session: DbSession,
) -> dict[str, Any] | JSONResponse:
    _require_owner_or_admin(role)
    try:
        user = await invite_member(
            session,
            UUID(tenant_id),
            email=body.email,
            display_name=body.display_name,
            role=body.role,
        )
    except TenantServiceError as exc:
        err = error_response(ErrorCode.VALIDATION_ERROR, request.state.request_id, exc.message)
        return JSONResponse(status_code=exc.status_code, content=err.model_dump())
    return _ok(request, _member_response(user).model_dump())


@router.patch("/me/users/{user_id}", response_model=None)
async def update_member(
    request: Request,
    user_id: str,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    body: UpdateMemberRoleRequest,
    session: DbSession,
) -> dict[str, Any] | JSONResponse:
    _require_owner(role)
    try:
        user = await update_member_role(session, UUID(tenant_id), UUID(user_id), role=body.role)
    except TenantServiceError as exc:
        err = error_response(ErrorCode.VALIDATION_ERROR, request.state.request_id, exc.message)
        return JSONResponse(status_code=exc.status_code, content=err.model_dump())
    return _ok(request, _member_response(user).model_dump())


@router.delete("/me/users/{user_id}", response_model=None)
async def deactivate_member_endpoint(
    request: Request,
    user_id: str,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    session: DbSession,
) -> dict[str, Any] | JSONResponse:
    _require_owner(role)
    if str(user_id) == str(CurrentUser):
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    try:
        await deactivate_member(session, UUID(tenant_id), UUID(user_id))
    except TenantServiceError as exc:
        err = error_response(ErrorCode.VALIDATION_ERROR, request.state.request_id, exc.message)
        return JSONResponse(status_code=exc.status_code, content=err.model_dump())
    return _ok(request, {"deactivated": user_id})
