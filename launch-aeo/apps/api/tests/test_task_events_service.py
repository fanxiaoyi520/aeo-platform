"""Task SSE stream service tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aeo_api.services import task_events
from aeo_api.services.task_service import TaskNotFoundError


def test_trace_and_task_payload_helpers() -> None:
    trace = task_events._trace_event_payload(
        "task-1",
        {"agent": "rules_agent", "status": "completed", "detail": {"hits": 2}},
    )
    assert trace["agent"] == "rules_agent"
    assert trace["detail"] == {"hits": 2}

    task = task_events._task_updated_payload(
        "task-1",
        {
            "status": "completed",
            "final_output": {"title": "Draft"},
            "error_message": None,
        },
    )
    assert task["status"] == "completed"
    assert task["generated"] == {"title": "Draft"}


@pytest.mark.asyncio
async def test_stream_task_events_emits_trace_and_status() -> None:
    service = AsyncMock()
    service.get_task = AsyncMock(
        return_value={
            "status": "running",
            "trace": [{"agent": "research_agent", "status": "completed"}],
            "error_message": None,
            "final_output": None,
        }
    )
    service.is_task_waiting_hitl = MagicMock(return_value=False)

    session = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    collected: list[tuple[str, dict[str, object]]] = []

    async def collect() -> None:
        async for event_name, payload in task_events.stream_task_events(
            service, session_factory, "task-1"
        ):
            collected.append((event_name, payload))
            if len(collected) >= 2:
                break

    with patch("aeo_api.services.task_events.asyncio.sleep", new_callable=AsyncMock):
        await collect()

    assert collected[0][0] == "agent.step"
    assert collected[1][0] == "task.updated"


@pytest.mark.asyncio
async def test_stream_task_events_not_found() -> None:
    service = AsyncMock()
    service.get_task = AsyncMock(side_effect=TaskNotFoundError())

    session = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    with pytest.raises(TaskNotFoundError):
        async for _ in task_events.stream_task_events(service, session_factory, "missing"):
            pass
