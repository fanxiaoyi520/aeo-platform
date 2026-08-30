from typing import Annotated, Any
from uuid import UUID

from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response, success_response
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import get_db_session
from aeo_api.schemas.tasks import (
    CreateTaskRequest,
    RejectTaskRequest,
    TaskListResponse,
    TaskResponse,
)
from aeo_api.services.task_events import stream_task_events
from aeo_api.services.task_service import TaskNotFoundError, TaskService, TaskStateError
from aeo_api.sse import format_sse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
_service = TaskService()
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _error_response(request: Request, code: ErrorCode, status_code: int) -> JSONResponse:
    body = error_response(code, request.state.request_id)
    return JSONResponse(status_code=status_code, content=body.model_dump())


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


@router.post("")
async def create_task(
    request: Request,
    body: CreateTaskRequest,
    session: DbSession,
) -> dict[str, Any]:
    data = await _service.create_task(session, payload=body.model_dump())
    return _ok(request, TaskResponse(**data).model_dump())


@router.get("")
async def list_tasks(
    request: Request,
    session: DbSession,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    data = await _service.list_tasks(session, page=page, page_size=page_size)
    return _ok(request, TaskListResponse(**data).model_dump())


@router.get("/{task_id}", response_model=None)
async def get_task(
    request: Request,
    task_id: UUID,
    session: DbSession,
) -> dict[str, Any] | JSONResponse:
    try:
        data = await _service.get_task(session, str(task_id))
    except TaskNotFoundError:
        return _error_response(request, ErrorCode.TASK_NOT_FOUND, 404)
    return _ok(request, TaskResponse(**data).model_dump())


@router.post("/{task_id}/approve", response_model=None)
async def approve_task(
    request: Request,
    task_id: UUID,
    session: DbSession,
) -> dict[str, Any] | JSONResponse:
    try:
        data = await _service.approve_task(session, str(task_id))
    except TaskNotFoundError:
        return _error_response(request, ErrorCode.TASK_NOT_FOUND, 404)
    except TaskStateError:
        return _error_response(request, ErrorCode.HITL_NOT_PENDING, 409)
    return _ok(request, TaskResponse(**data).model_dump())


@router.post("/{task_id}/reject", response_model=None)
async def reject_task(
    request: Request,
    task_id: UUID,
    body: RejectTaskRequest,
    session: DbSession,
) -> dict[str, Any] | JSONResponse:
    try:
        data = await _service.reject_task(session, str(task_id), feedback=body.feedback)
    except TaskNotFoundError:
        return _error_response(request, ErrorCode.TASK_NOT_FOUND, 404)
    except TaskStateError:
        return _error_response(request, ErrorCode.HITL_NOT_PENDING, 409)
    return _ok(request, TaskResponse(**data).model_dump())


@router.get("/{task_id}/events")
async def task_events(task_id: UUID) -> StreamingResponse:
    from aeo_api.db.models import async_session_factory

    async def event_stream() -> Any:
        try:
            async for event_name, payload in stream_task_events(
                _service, async_session_factory, str(task_id)
            ):
                yield format_sse(event_name, payload)
        except TaskNotFoundError:
            yield format_sse("error", {"message": "task not found", "task_id": str(task_id)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
