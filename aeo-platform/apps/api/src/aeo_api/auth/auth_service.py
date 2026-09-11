"""P5-02: Authentication service — signup, login, refresh."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.auth.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from aeo_api.auth.passwords import hash_password, verify_password
from aeo_api.db.tenant_models import Tenant, User


class AuthError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


async def create_tenant(session: AsyncSession, name: str, slug: str) -> Tenant:
    existing = await session.execute(select(Tenant).where(Tenant.slug == slug))
    if existing.scalar_one_or_none():
        raise AuthError(f"Tenant slug '{slug}' already exists")
    tenant = Tenant(id=uuid.uuid4(), name=name, slug=slug)
    session.add(tenant)
    await session.flush()
    return tenant


async def signup(
    session: AsyncSession,
    email: str,
    password: str,
    display_name: str | None,
    tenant_name: str,
    tenant_slug: str,
) -> tuple[User, Tenant]:
    tenant = await create_tenant(session, tenant_name, tenant_slug)

    existing_user = await session.execute(
        select(User).where(User.tenant_id == tenant.id, User.email == email)
    )
    if existing_user.scalar_one_or_none():
        raise AuthError(f"Email '{email}' already registered in this tenant")

    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=hash_password(password),
        display_name=display_name,
        role="owner",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user, tenant


async def login(session: AsyncSession, email: str, password: str) -> tuple[User, str, str]:
    result = await session.execute(select(User).where(User.email == email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid credentials")

    user.last_login_at = datetime.now(UTC)
    await session.flush()

    access_token = create_access_token(user.id, user.tenant_id, user.role)
    refresh_token = create_refresh_token(user.id, user.tenant_id)
    return user, access_token, refresh_token


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> tuple[str, str]:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise AuthError("Invalid refresh token") from None

    if payload.type != "refresh":
        raise AuthError("Token is not a refresh token")

    result = await session.execute(
        select(User).where(User.id == payload.sub, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("User not found")

    new_access = create_access_token(user.id, user.tenant_id, user.role)
    new_refresh = create_refresh_token(user.id, user.tenant_id)
    return new_access, new_refresh


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
