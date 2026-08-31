"""Tests for task SSE helpers."""

import json

from aeo_api.sse import format_sse


def test_format_sse_agent_step() -> None:
    message = format_sse(
        "agent.step",
        {
            "task_id": "task-1",
            "agent": "research_agent",
            "status": "completed",
            "timestamp": "2026-08-30T01:00:00+00:00",
            "detail": {},
        },
    )
    assert message.startswith("event: agent.step\n")
    data_line = message.split("data: ", 1)[1].strip()
    payload = json.loads(data_line)
    assert payload["agent"] == "research_agent"
