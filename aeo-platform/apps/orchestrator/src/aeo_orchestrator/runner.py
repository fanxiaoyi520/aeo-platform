"""CLI/API shared runner — execute listing graph until HITL or completion."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from aeo_orchestrator.graph import (
    build_ads_graph,
    build_graph,
    build_image_copy_graph,
    build_ops_graph,
    build_selection_graph,
    build_tiktok_video_graph,
)
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
    result = await compiled.ainvoke(state, config={"configurable": {"thread_id": resolved_id}})
    return result  # type: ignore[return-value]


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


async def run_image_copy_task(
    *,
    sku: str,
    platform: PlatformChoice = "amazon",
    market: str = "US",
    product_info: dict[str, Any] | None = None,
    task_id: str | None = None,
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState] | None = None,
) -> TaskState:
    """Run the image copywriting graph (single image_copy_agent node)."""
    resolved_id = task_id or str(uuid.uuid4())
    compiled = graph or build_image_copy_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id=resolved_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info,
    )
    result = await compiled.ainvoke(state, config={"configurable": {"thread_id": resolved_id}})
    return result  # type: ignore[return-value]


def serialize_image_copy_result(state: TaskState) -> dict[str, Any]:
    image_copy = state.get("image_copy") or {}
    return {
        "task_id": state["task_id"],
        "sku": state["sku"],
        "platform": state["platform"],
        "market": state.get("market", "US"),
        "image_copy": image_copy,
        "trace": state.get("trace", []),
    }


async def run_tiktok_video_task(
    *,
    sku: str,
    platform: PlatformChoice = "tiktok",
    market: str = "US",
    product_info: dict[str, Any] | None = None,
    task_id: str | None = None,
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState] | None = None,
) -> TaskState:
    """Run the TikTok video script graph (single tiktok_video_agent node)."""
    resolved_id = task_id or str(uuid.uuid4())
    compiled = graph or build_tiktok_video_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id=resolved_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info,
    )
    result = await compiled.ainvoke(state, config={"configurable": {"thread_id": resolved_id}})
    return result  # type: ignore[return-value]


def serialize_tiktok_video_result(state: TaskState) -> dict[str, Any]:
    tiktok_video = state.get("tiktok_video") or {}
    return {
        "task_id": state["task_id"],
        "sku": state["sku"],
        "platform": state["platform"],
        "market": state.get("market", "US"),
        "tiktok_video": tiktok_video,
        "trace": state.get("trace", []),
    }


async def run_selection_to_content_task(
    *,
    sku: str,
    platform: PlatformChoice = "amazon",
    market: str = "US",
    product_info: dict[str, Any] | None = None,
    task_id: str | None = None,
) -> TaskState:
    """Run the full selection → listing → image_copy → tiktok_video pipeline."""
    resolved_id = task_id or str(uuid.uuid4())
    state = initial_state(
        task_id=resolved_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info,
    )

    selection_graph = build_selection_graph(checkpointer=MemorySaver())
    state = await selection_graph.ainvoke(  # type: ignore[assignment]
        state,
        config={"configurable": {"thread_id": resolved_id}},
    )

    listing_graph = build_runner_graph()
    listing_result = await run_until_hitl(listing_graph, state)
    if is_waiting_hitl(listing_graph, resolved_id):
        listing_result = await approve_hitl(listing_graph, resolved_id)
    state = listing_result

    image_copy_graph = build_image_copy_graph(checkpointer=MemorySaver())
    state = await image_copy_graph.ainvoke(  # type: ignore[assignment]
        state,
        config={"configurable": {"thread_id": resolved_id}},
    )

    tiktok_graph = build_tiktok_video_graph(checkpointer=MemorySaver())
    state = await tiktok_graph.ainvoke(  # type: ignore[assignment]
        state,
        config={"configurable": {"thread_id": resolved_id}},
    )

    return state


def serialize_selection_to_content_result(state: TaskState) -> dict[str, Any]:
    stages_completed: list[str] = []
    if state.get("selection"):
        stages_completed.append("selection")
    if state.get("generated"):
        stages_completed.append("listing")
    if state.get("image_copy"):
        stages_completed.append("image_copy")
    if state.get("tiktok_video"):
        stages_completed.append("tiktok_video")

    return {
        "task_id": state["task_id"],
        "sku": state["sku"],
        "platform": state["platform"],
        "market": state.get("market", "US"),
        "selection": state.get("selection"),
        "generated": state.get("generated"),
        "image_copy": state.get("image_copy"),
        "tiktok_video": state.get("tiktok_video"),
        "stages_completed": stages_completed,
        "trace": state.get("trace", []),
    }


async def run_ads_task(
    *,
    sku: str,
    platform: PlatformChoice = "amazon",
    market: str = "US",
    product_info: dict[str, Any] | None = None,
    task_id: str | None = None,
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState] | None = None,
) -> TaskState:
    """Run the ads analysis graph (single ads_agent node)."""
    resolved_id = task_id or str(uuid.uuid4())
    compiled = graph or build_ads_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id=resolved_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info,
    )
    result = await compiled.ainvoke(state, config={"configurable": {"thread_id": resolved_id}})
    return result  # type: ignore[return-value]


def serialize_ads_result(state: TaskState) -> dict[str, Any]:
    ads = state.get("ads") or {}
    return {
        "task_id": state["task_id"],
        "sku": state["sku"],
        "platform": state["platform"],
        "market": state.get("market", "US"),
        "ads": ads,
        "trace": state.get("trace", []),
    }


async def run_ops_task(
    *,
    sku: str,
    platform: PlatformChoice = "amazon",
    market: str = "US",
    product_info: dict[str, Any] | None = None,
    task_id: str | None = None,
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState] | None = None,
) -> TaskState:
    """Run the operations analysis graph (single operations_agent node)."""
    resolved_id = task_id or str(uuid.uuid4())
    compiled = graph or build_ops_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id=resolved_id,
        platform=platform,
        sku=sku,
        market=market,
        product_info=product_info,
    )
    result = await compiled.ainvoke(state, config={"configurable": {"thread_id": resolved_id}})
    return result  # type: ignore[return-value]


def serialize_ops_result(state: TaskState) -> dict[str, Any]:
    ops = state.get("ops") or {}
    return {
        "task_id": state["task_id"],
        "sku": state["sku"],
        "platform": state["platform"],
        "market": state.get("market", "US"),
        "ops": ops,
        "trace": state.get("trace", []),
    }
