from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateTaskRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=128)
    platform: Literal["amazon", "tiktok"]
    market: str = Field(default="US", max_length=16)
    product_info: dict[str, Any] = Field(default_factory=dict)


class RejectTaskRequest(BaseModel):
    feedback: str = Field(min_length=1, max_length=2000)


class ApproveTaskRequest(BaseModel):
    listing: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    id: str
    sku: str
    platform: str
    market: str
    status: str
    product_info: dict[str, Any]
    trace: list[Any]
    generated: dict[str, Any] | None = None
    final_output: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
