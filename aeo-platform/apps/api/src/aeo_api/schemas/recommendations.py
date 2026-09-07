"""MV3-08: Recommendation API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AdsResponse(BaseModel):
    task_id: str = ""
    sku: str = ""
    platform: str = "amazon"
    market: str = "US"
    ads: dict[str, Any] = Field(default_factory=dict)
    trace: list[Any] = Field(default_factory=list)


class OpsResponse(BaseModel):
    task_id: str = ""
    sku: str = ""
    platform: str = "amazon"
    market: str = "US"
    ops: dict[str, Any] = Field(default_factory=dict)
    trace: list[Any] = Field(default_factory=list)


class LinkageRecommendationItem(BaseModel):
    campaign_id: str
    sku: str
    stock_status: str
    current_budget: Any
    suggested_budget: Any
    budget_change_percent: float
    reason: str = ""
    urgency: str = "low"


class LinkageResponse(BaseModel):
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
