"""MV2-03 — market intelligence API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class CompetitorSnapshotInput(BaseModel):
    asin: str
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None


class ScanRequest(BaseModel):
    sku: str
    platform: str = "amazon"
    marketplace: str = "US"
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None
    category: str | None = None
    brand: str | None = None
    has_title: bool = False
    has_bullets: bool = False
    has_keywords: bool = False
    has_images: bool = False
    previous_competitors: list[CompetitorSnapshotInput] = Field(default_factory=list)
    current_competitors: list[CompetitorSnapshotInput] = Field(default_factory=list)
    price_change_threshold: float = 0.05


class DiffChangeResponse(BaseModel):
    asin: str
    field: str
    old_value: float | int | None = None
    new_value: float | int | None = None
    delta: float | int | None = None


class DiffResponse(BaseModel):
    sku: str
    changes: list[DiffChangeResponse]
    new_listings: list[dict[str, Any]]
    removed_listings: list[dict[str, Any]]
    has_significant_change: bool


class SelectionResponse(BaseModel):
    sku: str
    platform: str
    marketplace: str
    total_score: float
    demand_score: float
    competition_score: float
    profitability_score: float
    completeness_score: float
    competitor_count: int
    recommendation: str
    detail: dict[str, Any] | None = None


class ScanResponse(BaseModel):
    sku: str
    diff: DiffResponse
    selection: SelectionResponse
    suggested_actions: list[str]
    scanned_at: str


class CreateScheduleRequest(BaseModel):
    job_id: str
    sku: str
    cron_expression: str
    enabled: bool = True
    payload: dict[str, Any] | None = None


class ScheduleResponse(BaseModel):
    id: str
    job_id: str
    sku: str
    cron_expression: str
    enabled: bool
    payload: dict[str, Any] | None = None
    last_run_at: str | None = None
    next_run_at: str | None = None
    created_at: str


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]
    total: int = Field(ge=0)
