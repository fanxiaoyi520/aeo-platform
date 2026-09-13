"""P5-07: Tenant admin service — manage tenant and members."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.auth.passwords import hash_password
from aeo_api.db.tenant_models import Tenant, User


class TenantServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def get_tenant(session: AsyncSession, tenant_id: UUID) -> Tenant:
    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise TenantServiceError("Tenant not found", status_code=404)
    return tenant


async def update_tenant(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    name: str | None = None,
    settings: dict[str, Any] | None = None,
) -> Tenant:
    tenant = await get_tenant(session, tenant_id)
    if name is not None:
        tenant.name = name
    if settings is not None:
        tenant.settings = settings
    await session.flush()
    await session.refresh(tenant)
    return tenant


async def list_members(session: AsyncSession, tenant_id: UUID) -> list[User]:
    result = await session.execute(
        select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
    )
    return list(result.scalars().all())


async def invite_member(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    email: str,
    display_name: str | None = None,
    role: str = "member",
    initial_password: str = "changeme-temp",
) -> User:
    existing = await session.execute(
        select(User).where(User.tenant_id == tenant_id, User.email == email)
    )
    if existing.scalar_one_or_none():
        raise TenantServiceError(f"Email '{email}' already exists in this tenant")

    user = User(
        tenant_id=tenant_id,
        email=email,
        hashed_password=hash_password(initial_password),
        display_name=display_name,
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def update_member_role(
    session: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    *,
    role: str,
) -> User:
    result = await session.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise TenantServiceError("Member not found", status_code=404)
    user.role = role
    await session.flush()
    await session.refresh(user)
    return user


async def deactivate_member(
    session: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
) -> None:
    result = await session.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise TenantServiceError("Member not found", status_code=404)
    user.is_active = False
    await session.flush()
