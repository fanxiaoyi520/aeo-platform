"""SSE stream for task trace and status updates."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from aeo_api.services.task_service import TaskNotFoundError, TaskService

POLL_INTERVAL_SECONDS = 2.0


def _trace_event_payload(task_id: str, event: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "agent": event.get("agent", "unknown"),
        "status": event.get("status", "unknown"),
        "timestamp": event.get("timestamp"),
        "detail": event.get("detail") or {},
    }


def _task_updated_payload(task_id: str, task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": task.get("status"),
        "error_message": task.get("error_message"),
        "final_output": task.get("final_output"),
        "generated": _extract_generated_preview(task),
    }


def _extract_generated_preview(task: dict[str, Any]) -> dict[str, Any] | None:
    final_output = task.get("final_output")
    if isinstance(final_output, dict) and final_output.get("title"):
        return final_output
    return None


async def stream_task_events(
    service: TaskService,
    session_factory: object,
    task_id: str,
) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    """Yield (event_name, data) tuples for SSE consumers."""
    async with session_factory() as session:  # type: ignore[operator]
        try:
            await service.get_task(session, task_id)
        except TaskNotFoundError:
            raise

    sent_trace_count = 0
    last_status: str | None = None

    while True:
        async with session_factory() as session:  # type: ignore[operator]
            task = await service.get_task(session, task_id)

        if service.is_task_waiting_hitl(task_id) and task.get("status") != "waiting_hitl":
            task = {**task, "status": "waiting_hitl"}

        trace = task.get("trace")
        if not isinstance(trace, list):
            trace = []

        for event in trace[sent_trace_count:]:
            if isinstance(event, dict):
                yield "agent.step", _trace_event_payload(task_id, event)
        sent_trace_count = len(trace)

        status = task.get("status")
        if status != last_status:
            yield "task.updated", _task_updated_payload(task_id, task)
            last_status = str(status) if status is not None else None

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
