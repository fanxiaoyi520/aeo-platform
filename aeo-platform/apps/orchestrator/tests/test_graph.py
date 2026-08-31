from typing import cast

import pytest
from aeo_orchestrator import build_graph, initial_state
from aeo_orchestrator.hitl import approve_hitl
from aeo_orchestrator.state import TaskStatus
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from llm_fixtures import patch_generate_instructor


def _thread_config(thread_id: str) -> RunnableConfig:
    return cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})


@pytest.mark.asyncio
async def test_graph_runs_until_hitl_interrupt() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="task-1",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B001"], "keywords": ["wireless earbuds"]},
    )
    config = _thread_config("task-1")

    with patch_generate_instructor():
        result = await graph.ainvoke(state, config=config)

    assert result["research"] is not None
    assert result["rules"] is not None
    assert result["generated"] is not None
    assert result["compliance"] is not None
    compliance = result["compliance"]
    assert isinstance(compliance, dict)
    assert compliance.get("passed") is True
    assert len(result["trace"]) >= 4

    snapshot = graph.get_state(config)
    assert snapshot.next == ("human_review",)


@pytest.mark.asyncio
async def test_graph_resumes_after_hitl() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="task-2",
        platform="tiktok",
        sku="DEMO-002",
        product_info={"competitor_asins": ["B002"], "keywords": ["wireless earbuds"]},
    )
    config = _thread_config("task-2")

    with patch_generate_instructor():
        await graph.ainvoke(state, config=config)
        resumed = await approve_hitl(graph, "task-2")

    assert resumed["status"] == TaskStatus.COMPLETED
    assert resumed["final_output"] is not None
