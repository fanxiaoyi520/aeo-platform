"""MV2-01 — selection scoring API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class CompetitorInput(BaseModel):
    asin: str
    price: float | None = None
    rating: float | None = None
    review_count: int | None = None


class CompetitorListingResponse(BaseModel):
    id: str
    asin: str
    sku: str
    platform: str
    marketplace: str
    title: str | None = None
    brand: str | None = None
    price: str | None = None
    currency: str = "USD"
    rating: float | None = None
    review_count: int | None = None
    category: str | None = None
    data_source: str = "mock"
    created_at: str


class CompetitorListResponse(BaseModel):
    items: list[CompetitorListingResponse]
    total: int = Field(ge=0)


class AddCompetitorRequest(BaseModel):
    asin: str
    sku: str
    platform: str = "amazon"
    marketplace: str = "US"
    title: str | None = None
    brand: str | None = None
    price: str | None = None
    currency: str = "USD"
    rating: float | None = None
    review_count: int | None = None
    bullet_points: list[str] | None = None
    category: str | None = None


class ScoreProductRequest(BaseModel):
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
    competitors: list[CompetitorInput] = Field(default_factory=list)


class SelectionScoreResponse(BaseModel):
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
    scored_at: str


class SelectionScoreListResponse(BaseModel):
    items: list[SelectionScoreResponse]
    total: int = Field(ge=0)
