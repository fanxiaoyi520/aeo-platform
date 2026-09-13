"""P5-05: Automatic tenant query isolation.

Provides helpers for tenant-scoped queries: `apply_tenant_filter()` for explicit
filtering, and utilities to detect tenant-scoped models.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Mapper
from sqlalchemy.sql import Select

from aeo_api.auth.context import current_tenant_id
from aeo_api.db.tenant_models import SYSTEM_TENANT_ID


def get_current_tenant() -> str:
    return current_tenant_id.get() or SYSTEM_TENANT_ID


def is_system_tenant() -> bool:
    return get_current_tenant() == SYSTEM_TENANT_ID


def has_tenant_column(model: type) -> bool:
    mapper: Mapper[Any] | None = inspect(model, raiseerr=False)
    if mapper is None:
        return False
    return hasattr(mapper, "columns") and "tenant_id" in mapper.columns


def apply_tenant_filter(stmt: Any, tenant_id: str | None = None) -> Any:
    tid = tenant_id or get_current_tenant()
    if tid == SYSTEM_TENANT_ID:
        return stmt
    if isinstance(stmt, Select):
        for desc in stmt.column_descriptions:
            entity = desc.get("entity")
            if entity is not None and has_tenant_column(entity):
                stmt = stmt.where(entity.tenant_id == tid)
    return stmt
