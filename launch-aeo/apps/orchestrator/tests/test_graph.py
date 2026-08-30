from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator import build_graph, initial_state
from aeo_orchestrator.state import TaskStatus
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

_SAMPLE_JSON = """{
  "title": "LAUNCH X431 Pro OBD2 Scanner Diagnostic Tool",
  "bullets": [
    "FULL SYSTEM DIAGNOSIS for engine and ABS codes",
    "LIVE DATA STREAM for faster troubleshooting",
    "WIDE OBD2 COVERAGE for most 1996+ vehicles",
    "PROFESSIONAL GRADE tool trusted by mechanics",
    "EASY TO USE with intuitive menus"
  ],
  "search_terms": "obd2 scanner diagnostic x431",
  "description": "Professional OBD2 scanner for workshops."
}"""


def _thread_config(thread_id: str) -> RunnableConfig:
    return cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})


@pytest.mark.asyncio
async def test_graph_runs_until_hitl_interrupt() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="task-1",
        platform="amazon",
        sku="X431",
        product_info={"competitor_asins": ["B001"], "keywords": ["obd2"]},
    )
    config = _thread_config("task-1")

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_JSON, model="test")

    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider):
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
        sku="CRP123",
        product_info={"competitor_asins": ["B002"], "keywords": ["scanner"]},
    )
    config = _thread_config("task-2")

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_JSON, model="test")

    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider):
        await graph.ainvoke(state, config=config)
        resumed = await graph.ainvoke(None, config=config)

    assert resumed["status"] == TaskStatus.COMPLETED
    assert resumed["final_output"] is not None
