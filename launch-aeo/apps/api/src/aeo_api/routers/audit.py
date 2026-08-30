from typing import Annotated, Any

from aeo_shared.responses import success_response
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import get_db_session
from aeo_api.schemas.audit import AuditLogItem, AuditLogListResponse
from aeo_api.services.audit_service import HITL_ACTIONS, AuditService

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit"])
_service = AuditService()
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("")
async def list_audit_logs(
    request: Request,
    session: DbSession,
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=100),
) -> dict[str, Any]:
    if action:
        actions = [item.strip() for item in action.split(",") if item.strip()]
    else:
        actions = list(HITL_ACTIONS)
    items = await _service.list_logs(session, actions=actions, limit=limit)
    serialized = [AuditLogItem.model_validate(item) for item in items]
    data = AuditLogListResponse(items=serialized, total=len(serialized)).model_dump()
    return success_response(data, request.state.request_id).model_dump()
