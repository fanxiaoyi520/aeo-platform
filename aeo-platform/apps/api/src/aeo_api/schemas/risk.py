from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskEvaluateRequest(BaseModel):
    action: str
    context: dict[str, Any] | None = None
    actor: str = "api"
    task_id: str | None = None


class RiskDecisionResponse(BaseModel):
    allowed: bool
    effect: Literal["allow", "require_hitl", "deny"]
    risk_level: Literal["L0", "L1", "L2"]
    rule_id: str
    message: str = ""


class RiskAuditItem(BaseModel):
    id: str
    action: str
    actor: str
    detail: dict[str, Any] | None
    created_at: str


class RiskAuditListResponse(BaseModel):
    items: list[RiskAuditItem]
    total: int = Field(ge=0)
