"""MV1-05 — Risk evaluation and audit API."""

from typing import Annotated, Any

from aeo_shared.responses import success_response
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import get_db_session
from aeo_api.schemas.risk import (
    RiskAuditItem,
    RiskAuditListResponse,
    RiskDecisionResponse,
    RiskEvaluateRequest,
)
from aeo_api.services.audit_service import AuditService
from aeo_api.services.risk_engine import RiskEngine

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])
_engine = RiskEngine()
_service = AuditService()
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("/evaluate")
async def evaluate_risk(
    request: Request,
    session: DbSession,
    body: RiskEvaluateRequest,
) -> dict[str, Any]:
    """Evaluate an action against risk rules."""
    decision = await _engine.evaluate(
        session,
        action=body.action,
        context=body.context,
        actor=body.actor,
        task_id=body.task_id,
    )
    response = RiskDecisionResponse(
        allowed=decision.allowed,
        effect=decision.effect.value,
        risk_level=decision.risk_level.value,
        rule_id=decision.rule_id,
        message=decision.message,
    )
    return success_response(response.model_dump(), request.state.request_id).model_dump()


@router.get("/audit")
async def list_risk_audit(
    request: Request,
    session: DbSession,
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=100),
) -> dict[str, Any]:
    """List risk evaluation audit logs."""
    items = await _service.list_risk_logs(session, evaluated_action=action, limit=limit)
    serialized = [RiskAuditItem.model_validate(item) for item in items]
    data = RiskAuditListResponse(items=serialized, total=len(serialized)).model_dump()
    return success_response(data, request.state.request_id).model_dump()
