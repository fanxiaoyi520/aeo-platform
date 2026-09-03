"""CLI/API shared runner — execute listing graph until HITL or completion."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from aeo_orchestrator.graph import build_graph, build_selection_graph
from aeo_orchestrator.hitl import approve_hitl, is_waiting_hitl, run_until_hitl
from aeo_orchestrator.state import TaskState, TaskStatus, initial_state

PlatformChoice = Literal["amazon", "tiktok"]


def build_runner_graph() -> CompiledStateGraph[TaskState, None, TaskState, TaskState]:
    return build_graph(checkpointer=MemorySaver())


async def run_listing_task(
    *,
    sku: str,
    platform: PlatformChoice = "amazon",
    market: str = "US",
    product_info: dict[str, Any] | None = None,
    task_id: str | None = None,
    auto_approve: bool = False,
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState] | None = None,
) -> TaskState:
    """Run the listing graph; optionally auto-approve HITL for non-interactive CLI."""
    resolved_id = task_id or str(uuid.uuid4())
    compiled = graph or build_runner_graph()
    state = initial_state(
        task_id=resolved_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info,
    )
    result = await run_until_hitl(compiled, state)
    if auto_approve and is_waiting_hitl(compiled, resolved_id):
        result = await approve_hitl(compiled, resolved_id)
    return result


async def run_selection_task(
    *,
    sku: str,
    platform: PlatformChoice = "amazon",
    market: str = "US",
    product_info: dict[str, Any] | None = None,
    task_id: str | None = None,
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState] | None = None,
) -> TaskState:
    """Run the selection analysis graph (single selection_agent node)."""
    resolved_id = task_id or str(uuid.uuid4())
    compiled = graph or build_selection_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id=resolved_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info,
    )
    return await compiled.ainvoke(state, config={"configurable": {"thread_id": resolved_id}})


def serialize_run_result(state: TaskState, *, waiting_hitl: bool) -> dict[str, Any]:
    status = state.get("status", TaskStatus.RUNNING)
    status_value = status.value if isinstance(status, TaskStatus) else str(status)
    if waiting_hitl:
        status_value = TaskStatus.WAITING_HITL.value

    return {
        "task_id": state["task_id"],
        "sku": state["sku"],
        "platform": state["platform"],
        "market": state.get("market", "US"),
        "status": status_value,
        "waiting_hitl": waiting_hitl,
        "degraded_mode": bool(state.get("degraded_mode", False)),
        "retry_count": int(state.get("retry_count", 0)),
        "final_output": state.get("final_output"),
        "generated": state.get("generated"),
        "compliance": state.get("compliance"),
        "trace": state.get("trace", []),
    }


def serialize_selection_result(state: TaskState) -> dict[str, Any]:
    selection = state.get("selection") or {}
    return {
        "task_id": state["task_id"],
        "sku": state["sku"],
        "platform": state["platform"],
        "market": state.get("market", "US"),
        "selection": selection,
        "trace": state.get("trace", []),
    }
