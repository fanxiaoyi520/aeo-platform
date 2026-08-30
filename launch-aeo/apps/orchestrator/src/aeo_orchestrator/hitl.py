"""HITL helpers — run until interrupt, approve, or reject with feedback."""

from __future__ import annotations

from typing import cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from aeo_orchestrator.state import TaskState, TaskStatus


def task_thread_config(task_id: str) -> RunnableConfig:
    return cast(RunnableConfig, {"configurable": {"thread_id": task_id}})


async def run_until_hitl(
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState],
    state: TaskState,
) -> TaskState:
    """Execute the graph until the HITL interrupt before human_review."""
    config = task_thread_config(state["task_id"])
    result = await graph.ainvoke(state, config=config)
    return cast(TaskState, result)


async def approve_hitl(
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState],
    task_id: str,
) -> TaskState:
    """Resume a paused task after human approval."""
    config = task_thread_config(task_id)
    graph.update_state(config, {"hitl_decision": "approve"})
    result = await graph.ainvoke(None, config=config)
    return cast(TaskState, result)


async def reject_hitl(
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState],
    task_id: str,
    feedback: str,
) -> TaskState:
    """Resume with rejection feedback and route back to generate_agent."""
    config = task_thread_config(task_id)
    graph.update_state(
        config,
        {
            "hitl_decision": "reject",
            "human_feedback": feedback,
            "compliance": None,
            "status": TaskStatus.RUNNING,
        },
    )
    result = await graph.ainvoke(None, config=config)
    return cast(TaskState, result)


def is_waiting_hitl(
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState],
    task_id: str,
) -> bool:
    """Return True when the graph is paused before human_review."""
    snapshot = graph.get_state(task_thread_config(task_id))
    return snapshot.next == ("human_review",)
