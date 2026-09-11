"""P5-03: RBAC dependencies for FastAPI."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request

ROLE_HIERARCHY: dict[str, int] = {"owner": 3, "admin": 2, "member": 1}


def get_current_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return str(user_id)


def get_current_tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return str(tenant_id)


def get_current_role(request: Request) -> str:
    return getattr(request.state, "user_role", "member")


CurrentUser = Annotated[str, Depends(get_current_user_id)]
CurrentTenant = Annotated[str, Depends(get_current_tenant_id)]
CurrentRole = Annotated[str, Depends(get_current_role)]
