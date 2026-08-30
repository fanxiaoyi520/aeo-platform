from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator import build_graph, initial_state
from aeo_orchestrator.hitl import approve_hitl, is_waiting_hitl, reject_hitl, run_until_hitl
from aeo_orchestrator.state import TaskStatus
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


def _mock_llm() -> AsyncMock:
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=_SAMPLE_JSON, model="test")
    return provider


@pytest.mark.asyncio
async def test_run_until_hitl_pauses_before_human_review() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="hitl-1",
        platform="amazon",
        sku="X431",
        product_info={"competitor_asins": ["B001"], "keywords": ["obd2"]},
    )
    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=_mock_llm()):
        await run_until_hitl(graph, state)
    assert is_waiting_hitl(graph, "hitl-1") is True


@pytest.mark.asyncio
async def test_approve_hitl_completes_task() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(
        task_id="hitl-2",
        platform="amazon",
        sku="X431",
        product_info={"competitor_asins": ["B001"], "keywords": ["obd2"]},
    )
    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=_mock_llm()):
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
        sku="X431",
        product_info={"competitor_asins": ["B001"], "keywords": ["obd2"]},
    )
    provider = _mock_llm()
    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=provider):
        await run_until_hitl(graph, state)
        result = await reject_hitl(graph, "hitl-3", "Shorten the title")
    assert result["human_feedback"] == "Shorten the title"
    assert provider.chat.call_count >= 2
