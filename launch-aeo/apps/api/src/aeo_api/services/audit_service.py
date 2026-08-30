from __future__ import annotations

import uuid
from typing import Any

from aeo_shared.redaction import redact_value
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import AuditLog

HITL_ACTIONS: tuple[str, ...] = ("hitl_approve", "hitl_reject")


def _serialize_audit_log(entry: AuditLog) -> dict[str, Any]:
    return {
        "id": str(entry.id),
        "task_id": str(entry.task_id) if entry.task_id else None,
        "action": entry.action,
        "actor": entry.actor,
        "detail": redact_value(entry.detail) if entry.detail else None,
        "created_at": entry.created_at.isoformat(),
    }


class AuditService:
    async def list_logs(
        self,
        session: AsyncSession,
        *,
        actions: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 100))
        if actions:
            query = query.where(AuditLog.action.in_(actions))
        result = await session.execute(query)
        return [_serialize_audit_log(entry) for entry in result.scalars().all()]

    async def record(
        self,
        session: AsyncSession,
        *,
        action: str,
        actor: str = "api",
        task_id: uuid.UUID | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        session.add(
            AuditLog(
                task_id=task_id,
                action=action,
                actor=actor,
                detail=detail,
            )
        )
