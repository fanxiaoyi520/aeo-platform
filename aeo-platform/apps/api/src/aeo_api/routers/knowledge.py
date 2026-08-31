from typing import Annotated, Any

from aeo_shared.responses import success_response
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import get_db_session
from aeo_api.schemas.knowledge import (
    KnowledgeDocumentItem,
    KnowledgeDocumentsResponse,
    KnowledgeReindexResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultItem,
    KnowledgeStatsResponse,
    KnowledgeUploadResponse,
)
from aeo_api.services.audit_service import AuditService
from aeo_api.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])
_service = KnowledgeService()
_audit = AuditService()
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


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


@router.get("/documents")
async def list_knowledge_documents(request: Request) -> dict[str, Any]:
    items = _service.list_documents()
    data = KnowledgeDocumentsResponse(
        items=[KnowledgeDocumentItem(**item) for item in items],
        total=len(items),
    )
    return success_response(data.model_dump(), request.state.request_id).model_dump()


@router.post("/upload")
async def upload_knowledge_document(
    request: Request,
    session: DbSession,
    file: Annotated[UploadFile, File()],
    category: Annotated[str, Form()] = "uploads",
) -> dict[str, Any]:
    content = await file.read()
    try:
        result = _service.upload_document(file.filename or "upload.bin", content, category=category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await _audit.record(
        session,
        action="knowledge_upload",
        detail={
            "source_file": result["source_file"],
            "category": result["category"],
            "size_bytes": result["size_bytes"],
        },
    )
    await session.commit()

    reindex_result = result["reindex"]
    data = KnowledgeUploadResponse(
        source_file=result["source_file"],
        size_bytes=result["size_bytes"],
        category=result["category"],
        reindex=KnowledgeReindexResponse(**reindex_result),
    )
    return success_response(data.model_dump(), request.state.request_id).model_dump()


@router.post("/reindex")
async def reindex_knowledge(request: Request, session: DbSession) -> dict[str, Any]:
    result = _service.reindex(reset=True)
    await _audit.record(
        session,
        action="knowledge_reindex",
        detail={"reset": True, **result},
    )
    await session.commit()
    return success_response(
        KnowledgeReindexResponse(**result).model_dump(),
        request.state.request_id,
    ).model_dump()
