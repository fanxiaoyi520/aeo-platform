"""MV2-03 — market intelligence API router."""

from typing import Annotated, Any

from aeo_orchestrator.nodes.market_intelligence import MarketIntelService, ScanInput
from aeo_shared.competitor_monitor import ListingSnapshot
from aeo_shared.cron_parser import next_run, parse_cron
from aeo_shared.responses import success_response
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import IntelligenceSchedule, get_db_session
from aeo_api.schemas.intelligence import (
    CreateScheduleRequest,
    ScanRequest,
    ScanResponse,
    ScheduleListResponse,
    ScheduleResponse,
)

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("/scan")
async def scan_market_intelligence(
    request: Request,
    body: ScanRequest,
) -> dict[str, Any]:
    """Run a one-shot market intelligence scan for a SKU."""
    service = MarketIntelService()
    prev = [
        ListingSnapshot(asin=c.asin, price=c.price, rating=c.rating, review_count=c.review_count)
        for c in body.previous_competitors
    ]
    curr = [
        ListingSnapshot(asin=c.asin, price=c.price, rating=c.rating, review_count=c.review_count)
        for c in body.current_competitors
    ]
    inp = ScanInput(
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
        previous_competitors=prev,
        current_competitors=curr,
        price_change_threshold=body.price_change_threshold,
    )
    report = service.scan(inp)
    data = ScanResponse(**report.to_dict()).model_dump()
    return success_response(data, request.state.request_id).model_dump()


@router.get("/schedules")
async def list_schedules(
    request: Request,
    session: DbSession,
    limit: int = 50,
) -> dict[str, Any]:
    """List all market intelligence cron schedules."""
    query = (
        select(IntelligenceSchedule).order_by(IntelligenceSchedule.created_at.desc()).limit(limit)
    )
    result = await session.execute(query)
    rows = result.scalars().all()
    items = [
        ScheduleResponse(
            id=str(row.id),
            job_id=row.job_id,
            sku=row.sku,
            cron_expression=row.cron_expression,
            enabled=row.enabled,
            payload=row.payload,
            last_run_at=row.last_run_at.isoformat() if row.last_run_at else None,
            next_run_at=row.next_run_at.isoformat() if row.next_run_at else None,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]
    data = ScheduleListResponse(items=items, total=len(items)).model_dump()
    return success_response(data, request.state.request_id).model_dump()


@router.post("/schedules")
async def create_schedule(
    request: Request,
    session: DbSession,
    body: CreateScheduleRequest,
) -> dict[str, Any]:
    """Create a new market intelligence cron schedule."""
    try:
        schedule = parse_cron(body.cron_expression)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    existing = await session.execute(
        select(IntelligenceSchedule).where(IntelligenceSchedule.job_id == body.job_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"job_id already exists: {body.job_id}")

    from datetime import UTC, datetime

    now = datetime.now(UTC)
    row = IntelligenceSchedule(
        job_id=body.job_id,
        sku=body.sku,
        cron_expression=body.cron_expression,
        enabled=body.enabled,
        payload=body.payload,
        next_run_at=next_run(schedule, now),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    item = ScheduleResponse(
        id=str(row.id),
        job_id=row.job_id,
        sku=row.sku,
        cron_expression=row.cron_expression,
        enabled=row.enabled,
        payload=row.payload,
        last_run_at=row.last_run_at.isoformat() if row.last_run_at else None,
        next_run_at=row.next_run_at.isoformat() if row.next_run_at else None,
        created_at=row.created_at.isoformat(),
    )
    return success_response(item.model_dump(), request.state.request_id).model_dump()


@router.delete("/schedules/{job_id}")
async def delete_schedule(
    request: Request,
    session: DbSession,
    job_id: str,
) -> dict[str, Any]:
    """Delete a market intelligence cron schedule."""
    result = await session.execute(
        select(IntelligenceSchedule).where(IntelligenceSchedule.job_id == job_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {job_id}")
    await session.delete(row)
    await session.commit()
    return success_response({"deleted": job_id}, request.state.request_id).model_dump()
