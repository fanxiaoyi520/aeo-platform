"""P5-04: Tenant context via contextvars (async-safe)."""

from contextvars import ContextVar

current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)
current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)
current_user_role: ContextVar[str] = ContextVar("current_user_role", default="member")
