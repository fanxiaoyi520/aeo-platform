import pytest
from aeo_orchestrator import build_graph, initial_state
from aeo_orchestrator.hitl import approve_hitl, is_waiting_hitl, reject_hitl, run_until_hitl
from aeo_orchestrator.state import TaskStatus
from langgraph.checkpoint.memory import MemorySaver
from llm_fixtures import patch_generate_instructor


@pytest.mark.asyncio
async def test_run_until_hitl_pauses_before_human_review() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="hitl-1",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B001"], "keywords": ["wireless earbuds"]},
    )
    with patch_generate_instructor():
        await run_until_hitl(graph, state)
    assert is_waiting_hitl(graph, "hitl-1") is True


@pytest.mark.asyncio
async def test_approve_hitl_completes_task() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="hitl-2",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B001"], "keywords": ["wireless earbuds"]},
    )
    with patch_generate_instructor():
        await run_until_hitl(graph, state)
        result = await approve_hitl(graph, "hitl-2")
    assert result["status"] == TaskStatus.COMPLETED
    assert result["final_output"] is not None


@pytest.mark.asyncio
async def test_reject_hitl_routes_back_to_generate() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="hitl-3",
        platform="amazon",
        sku="DEMO-001",
        product_info={"competitor_asins": ["B001"], "keywords": ["wireless earbuds"]},
    )
    with patch_generate_instructor() as client:
        await run_until_hitl(graph, state)
        result = await reject_hitl(graph, "hitl-3", "Shorten the title")
    assert result["human_feedback"] == "Shorten the title"
    assert client.chat.completions.create.await_count >= 2
