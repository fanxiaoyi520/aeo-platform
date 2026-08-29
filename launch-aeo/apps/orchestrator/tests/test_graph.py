from typing import cast

import pytest
from aeo_orchestrator import build_graph, initial_state
from aeo_orchestrator.state import TaskStatus
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver


def _thread_config(thread_id: str) -> RunnableConfig:
    return cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})


@pytest.mark.asyncio
async def test_graph_runs_until_hitl_interrupt() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(task_id="task-1", platform="amazon", sku="X431")
    config = _thread_config("task-1")

    result = await graph.ainvoke(state, config=config)

    assert result["research"] is not None
    assert result["rules"] is not None
    assert result["generated"] is not None
    assert result["compliance"] is not None
    assert len(result["trace"]) >= 4

    snapshot = graph.get_state(config)
    assert snapshot.next == ("human_review",)


@pytest.mark.asyncio
async def test_graph_resumes_after_hitl() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(task_id="task-2", platform="tiktok", sku="CRP123")
    config = _thread_config("task-2")

    await graph.ainvoke(state, config=config)
    resumed = await graph.ainvoke(None, config=config)

    assert resumed["status"] == TaskStatus.COMPLETED
    assert resumed["final_output"] is not None
