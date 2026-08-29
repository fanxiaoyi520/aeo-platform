from typing import Any

from aeo_shared.responses import success_response
from fastapi import APIRouter, Request

from aeo_api.schemas.knowledge import (
    KnowledgeReindexResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultItem,
    KnowledgeStatsResponse,
)
from aeo_api.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])
_service = KnowledgeService()


@router.post("/search")
async def search_knowledge(
    request: Request,
    body: KnowledgeSearchRequest,
) -> dict[str, Any]:
    results = _service.search(
        body.query,
        platform=body.platform,
        category=body.category,
        top_k=body.top_k,
    )
    data = KnowledgeSearchResponse(
        query=body.query,
        results=[
            KnowledgeSearchResultItem(
                doc_id=r.doc_id,
                content=r.content,
                score=r.score,
                category=r.category,
                platform=r.platform,
                source_file=r.source_file,
                chunk_index=r.chunk_index,
            )
            for r in results
        ],
        total=len(results),
    )
    return success_response(data.model_dump(), request.state.request_id).model_dump()


@router.get("/stats")
async def knowledge_stats(request: Request) -> dict[str, Any]:
    stats = _service.stats()
    return success_response(
        KnowledgeStatsResponse(**stats).model_dump(),
        request.state.request_id,
    ).model_dump()


@router.post("/reindex")
async def reindex_knowledge(request: Request) -> dict[str, Any]:
    result = _service.reindex(reset=True)
    return success_response(
        KnowledgeReindexResponse(**result).model_dump(),
        request.state.request_id,
    ).model_dump()
