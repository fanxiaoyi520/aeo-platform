"""MV1-05 — Risk engine service with audit integration."""

from __future__ import annotations

from typing import Any

from aeo_shared.risk_dsl import (
    RiskDecision,
    default_production_rule_set,
    evaluate_action,
)
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import AuditLog


class RiskEngine:
    """Evaluates actions against risk rules and records audit logs."""

    def __init__(self) -> None:
        self._rule_set = default_production_rule_set()

    async def evaluate(
        self,
        session: AsyncSession,
        *,
        action: str,
        context: dict[str, Any] | None = None,
        actor: str = "system",
        task_id: str | None = None,
    ) -> RiskDecision:
        """Evaluate an action against risk rules and record audit log."""
        decision = evaluate_action(action, context, self._rule_set)

        audit_detail = {
            "action": action,
            "context": context or {},
            "effect": decision.effect.value,
            "risk_level": decision.risk_level.value,
            "rule_id": decision.rule_id,
            "message": decision.message,
            "allowed": decision.allowed,
        }

        session.add(
            AuditLog(
                task_id=task_id,
                action="risk.evaluate",
                actor=actor,
                detail=audit_detail,
            )
        )

        return decision
