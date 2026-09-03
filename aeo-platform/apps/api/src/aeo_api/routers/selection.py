"""MV2-01 — selection scoring and competitor pool API."""

from typing import Annotated, Any

from aeo_shared.responses import success_response
from aeo_shared.selection_scoring import CompetitorData, SelectionInput, score_product
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import CompetitorListing, SelectionScore, get_db_session
from aeo_api.schemas.selection import (
    AddCompetitorRequest,
    CompetitorListingResponse,
    CompetitorListResponse,
    ScoreProductRequest,
    SelectionScoreListResponse,
    SelectionScoreResponse,
)

router = APIRouter(prefix="/api/v1/selection", tags=["selection"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/competitors")
async def list_competitors(
    request: Request,
    session: DbSession,
    sku: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """List competitor listings in the pool."""
    query = select(CompetitorListing).order_by(CompetitorListing.created_at.desc()).limit(limit)
    if sku:
        query = query.where(CompetitorListing.sku == sku)
    result = await session.execute(query)
    rows = result.scalars().all()
    items = [
        CompetitorListingResponse(
            id=str(row.id),
            asin=row.asin,
            sku=row.sku,
            platform=row.platform,
            marketplace=row.marketplace,
            title=row.title,
            brand=row.brand,
            price=row.price,
            currency=row.currency,
            rating=row.rating,
            review_count=row.review_count,
            category=row.category,
            data_source=row.data_source,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]
    data = CompetitorListResponse(items=items, total=len(items)).model_dump()
    return success_response(data, request.state.request_id).model_dump()


@router.post("/competitors")
async def add_competitor(
    request: Request,
    session: DbSession,
    body: AddCompetitorRequest,
) -> dict[str, Any]:
    """Add a competitor listing to the pool."""
    row = CompetitorListing(
        asin=body.asin,
        sku=body.sku,
        platform=body.platform,
        marketplace=body.marketplace,
        title=body.title,
        brand=body.brand,
        price=body.price,
        currency=body.currency,
        rating=body.rating,
        review_count=body.review_count,
        bullet_points=body.bullet_points,
        category=body.category,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    item = CompetitorListingResponse(
        id=str(row.id),
        asin=row.asin,
        sku=row.sku,
        platform=row.platform,
        marketplace=row.marketplace,
        title=row.title,
        brand=row.brand,
        price=row.price,
        currency=row.currency,
        rating=row.rating,
        review_count=row.review_count,
        category=row.category,
        data_source=row.data_source,
        created_at=row.created_at.isoformat(),
    )
    return success_response(item.model_dump(), request.state.request_id).model_dump()


@router.post("/score")
async def score_product_endpoint(
    request: Request,
    session: DbSession,
    body: ScoreProductRequest,
) -> dict[str, Any]:
    """Score a product candidate for selection."""
    competitors = [
        CompetitorData(
            asin=c.asin,
            price=c.price,
            rating=c.rating,
            review_count=c.review_count,
        )
        for c in body.competitors
    ]
    selection_input = SelectionInput(
        sku=body.sku,
        platform=body.platform,
        marketplace=body.marketplace,
        price=body.price,
        rating=body.rating,
        review_count=body.review_count,
        category=body.category,
        brand=body.brand,
        has_title=body.has_title,
        has_bullets=body.has_bullets,
        has_keywords=body.has_keywords,
        has_images=body.has_images,
        competitors=competitors,
    )
    result = score_product(selection_input)
    score_row = SelectionScore(
        sku=result.sku,
        platform=result.platform,
        marketplace=result.marketplace,
        total_score=result.total_score,
        demand_score=result.demand_score,
        competition_score=result.competition_score,
        profitability_score=result.profitability_score,
        completeness_score=result.completeness_score,
        competitor_count=result.competitor_count,
        detail=result.detail,
        recommendation=result.recommendation,
    )
    session.add(score_row)
    await session.commit()
    await session.refresh(score_row)
    response = SelectionScoreResponse(
        sku=result.sku,
        platform=result.platform,
        marketplace=result.marketplace,
        total_score=round(result.total_score, 2),
        demand_score=round(result.demand_score, 2),
        competition_score=round(result.competition_score, 2),
        profitability_score=round(result.profitability_score, 2),
        completeness_score=round(result.completeness_score, 2),
        competitor_count=result.competitor_count,
        recommendation=result.recommendation,
        detail=result.detail,
        scored_at=score_row.scored_at.isoformat(),
    )
    return success_response(response.model_dump(), request.state.request_id).model_dump()


@router.get("/scores")
async def list_scores(
    request: Request,
    session: DbSession,
    sku: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """List selection scoring history."""
    query = select(SelectionScore).order_by(SelectionScore.scored_at.desc()).limit(limit)
    if sku:
        query = query.where(SelectionScore.sku == sku)
    result = await session.execute(query)
    rows = result.scalars().all()
    items = [
        SelectionScoreResponse(
            sku=row.sku,
            platform=row.platform,
            marketplace=row.marketplace,
            total_score=round(row.total_score, 2),
            demand_score=round(row.demand_score, 2),
            competition_score=round(row.competition_score, 2),
            profitability_score=round(row.profitability_score, 2),
            completeness_score=round(row.completeness_score, 2),
            competitor_count=row.competitor_count,
            recommendation=row.recommendation,
            detail=row.detail,
            scored_at=row.scored_at.isoformat(),
        )
        for row in rows
    ]
    data = SelectionScoreListResponse(items=items, total=len(items)).model_dump()
    return success_response(data, request.state.request_id).model_dump()
