"""LangGraph task state — aligned with M03 §3 and 04_ARCHITECTURE_STANDARDS §7."""

from __future__ import annotations

import operator
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, TypedDict


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_HITL = "waiting_hitl"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTraceStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentTraceEvent(TypedDict):
    agent: str
    status: str
    timestamp: str
    detail: dict[str, Any]


Platform = Literal["amazon", "tiktok"]


class TaskState(TypedDict, total=False):
    task_id: str
    platform: Platform
    sku: str
    market: str
    product_info: dict[str, Any]
    research: dict[str, Any] | None
    rules: dict[str, Any] | None
    generated: dict[str, Any] | None
    compliance: dict[str, Any] | None
    human_feedback: str | None
    hitl_decision: Literal["approve", "reject"] | None
    final_output: dict[str, Any] | None
    retry_count: int
    degraded_mode: bool
    error: str | None
    trace: Annotated[list[AgentTraceEvent], operator.add]
    status: TaskStatus


def make_trace_event(
    agent: str,
    status: AgentTraceStatus | str,
    *,
    detail: dict[str, Any] | None = None,
) -> AgentTraceEvent:
    return {
        "agent": agent,
        "status": status.value if isinstance(status, AgentTraceStatus) else status,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": detail or {},
    }


def initial_state(
    *,
    task_id: str,
    platform: Platform,
    sku: str,
    market: str = "US",
    product_info: dict[str, Any] | None = None,
) -> TaskState:
    return TaskState(
        task_id=task_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info or {},
        research=None,
        rules=None,
        generated=None,
        compliance=None,
        human_feedback=None,
        hitl_decision=None,
        final_output=None,
        retry_count=0,
        degraded_mode=False,
        error=None,
        trace=[],
        status=TaskStatus.RUNNING,
    )
