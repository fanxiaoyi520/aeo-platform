"""Task orchestration service — graph execution + DB persistence."""

from __future__ import annotations

import uuid
from typing import Any, cast

import structlog
from aeo_orchestrator import build_graph, initial_state
from aeo_orchestrator.hitl import (
    approve_hitl,
    is_waiting_hitl,
    reject_hitl,
    run_until_hitl,
    task_thread_config,
)
from aeo_orchestrator.persistence import set_listing_saver
from aeo_orchestrator.state import TaskStatus as GraphTaskStatus
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import AuditLog, ListingVersion, Task, TaskStatus

logger = structlog.get_logger(__name__)


class TaskNotFoundError(Exception):
    pass


class TaskStateError(Exception):
    pass


def _serialize_task(
    task: Task,
    *,
    final_output: dict[str, Any] | None = None,
    generated: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": str(task.id),
        "sku": task.sku,
        "platform": task.platform,
        "market": task.market,
        "status": task.status,
        "product_info": task.product_info or {},
        "trace": task.trace or [],
        "final_output": final_output,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
    if generated is not None:
        payload["generated"] = generated
    return payload


class TaskService:
    def __init__(self) -> None:
        self._checkpointer = MemorySaver()
        self._graph = build_graph(checkpointer=self._checkpointer)
        self._listing_saver_registered = False

    def _ensure_listing_saver(self, session_factory: object) -> None:
        if self._listing_saver_registered:
            return

        async def _save_listing(task_id: str, content: dict[str, Any]) -> dict[str, Any]:
            async with session_factory() as session:  # type: ignore[operator]
                task_uuid = uuid.UUID(task_id)
                result = await session.execute(
                    select(func.max(ListingVersion.version)).where(
                        ListingVersion.task_id == task_uuid
                    )
                )
                current = result.scalar_one_or_none() or 0
                version = int(current) + 1
                listing = ListingVersion(task_id=task_uuid, version=version, content=content)
                session.add(listing)
                await session.commit()
                await session.refresh(listing)
                return {"id": str(listing.id), "version": version, "persisted": True}

        set_listing_saver(_save_listing)
        self._listing_saver_registered = True

    async def _get_task(self, session: AsyncSession, task_id: str) -> Task:
        task_uuid = uuid.UUID(task_id)
        task = await session.get(Task, task_uuid)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    async def _sync_task_from_graph(
        self,
        session: AsyncSession,
        task: Task,
        graph_state: dict[str, Any],
    ) -> dict[str, Any]:
        status = graph_state.get("status", TaskStatus.RUNNING)
        status_value = status.value if isinstance(status, GraphTaskStatus) else str(status)

        if is_waiting_hitl(self._graph, str(task.id)):
            status_value = TaskStatus.WAITING_HITL

        task.status = status_value
        task.trace = graph_state.get("trace", task.trace or [])
        task.error_message = graph_state.get("error")
        await session.commit()
        await session.refresh(task)
        final_output = graph_state.get("final_output")
        if isinstance(final_output, dict):
            return final_output
        return {}

    async def create_task(
        self, session: AsyncSession, *, payload: dict[str, Any]
    ) -> dict[str, Any]:
        from aeo_api.db.models import async_session_factory

        self._ensure_listing_saver(async_session_factory)

        task_id = uuid.uuid4()
        task = Task(
            id=task_id,
            sku=payload["sku"],
            platform=payload["platform"],
            market=payload.get("market", "US"),
            status=TaskStatus.RUNNING,
            product_info=payload.get("product_info") or {},
            trace=[],
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        state = initial_state(
            task_id=str(task.id),
            platform=payload["platform"],
            sku=payload["sku"],
            market=payload.get("market", "US"),
            product_info=payload.get("product_info") or {},
        )
        try:
            graph_state = await run_until_hitl(self._graph, state)
            final_output = await self._sync_task_from_graph(
                session, task, cast(dict[str, Any], graph_state)
            )
        except Exception as exc:
            logger.exception("task run failed", task_id=str(task.id))
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            await session.commit()
            await session.refresh(task)
            raise
        return _serialize_task(task, final_output=final_output or None)

    async def get_task(self, session: AsyncSession, task_id: str) -> dict[str, Any]:
        task = await self._get_task(session, task_id)
        snapshot = self._graph.get_state(task_thread_config(task_id))
        values = snapshot.values if snapshot.values else {}
        final_output = values.get("final_output")
        generated = values.get("generated")
        status = task.status
        if is_waiting_hitl(self._graph, task_id):
            status = TaskStatus.WAITING_HITL
        task.status = status
        return _serialize_task(
            task,
            final_output=final_output if isinstance(final_output, dict) else None,
            generated=generated if isinstance(generated, dict) else None,
        )

    async def list_tasks(
        self,
        session: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        total_result = await session.execute(select(func.count()).select_from(Task))
        total = int(total_result.scalar_one())

        result = await session.execute(
            select(Task).order_by(Task.created_at.desc()).offset(offset).limit(page_size)
        )
        items = [_serialize_task(task) for task in result.scalars().all()]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def approve_task(
        self,
        session: AsyncSession,
        task_id: str,
        *,
        listing: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = await self._get_task(session, task_id)
        if task.status != TaskStatus.WAITING_HITL:
            raise TaskStateError("approve")
        if not is_waiting_hitl(self._graph, task_id):
            raise TaskStateError("approve")

        if listing:
            self._graph.update_state(task_thread_config(task_id), {"generated": listing})

        graph_state = await approve_hitl(self._graph, task_id)
        final_output = await self._sync_task_from_graph(
            session, task, cast(dict[str, Any], graph_state)
        )
        session.add(
            AuditLog(
                task_id=task.id, action="hitl_approve", actor="api", detail={"task_id": task_id}
            )
        )
        await session.commit()
        return _serialize_task(task, final_output=final_output or None)

    async def reject_task(
        self,
        session: AsyncSession,
        task_id: str,
        *,
        feedback: str,
    ) -> dict[str, Any]:
        task = await self._get_task(session, task_id)
        if task.status != TaskStatus.WAITING_HITL:
            raise TaskStateError("reject")
        if not is_waiting_hitl(self._graph, task_id):
            raise TaskStateError("reject")

        graph_state = await reject_hitl(self._graph, task_id, feedback)
        final_output = await self._sync_task_from_graph(
            session, task, cast(dict[str, Any], graph_state)
        )
        session.add(
            AuditLog(
                task_id=task.id,
                action="hitl_reject",
                actor="api",
                detail={"task_id": task_id, "feedback": feedback},
            )
        )
        await session.commit()
        return _serialize_task(task, final_output=final_output or None)

    def is_task_waiting_hitl(self, task_id: str) -> bool:
        return is_waiting_hitl(self._graph, task_id)
