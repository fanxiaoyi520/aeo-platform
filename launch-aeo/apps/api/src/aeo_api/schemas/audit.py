from typing import Any

from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    id: str
    task_id: str | None
    action: str
    actor: str
    detail: dict[str, Any] | None
    created_at: str


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int = Field(ge=0)
