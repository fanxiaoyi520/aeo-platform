"""MS3 acceptance — CLI + graph flows per M03 §6."""

from __future__ import annotations

import json
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator import build_graph, initial_state
from aeo_orchestrator.cli import main
from aeo_orchestrator.hitl import approve_hitl, is_waiting_hitl
from aeo_orchestrator.nodes.compliance import MAX_COMPLIANCE_RETRIES
from aeo_orchestrator.runner import build_runner_graph, run_listing_task, serialize_run_result
from aeo_orchestrator.state import TaskStatus
from click.testing import CliRunner
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

_LLM_PATCH = "aeo_orchestrator.nodes.generate.get_llm_provider"

_VALID_JSON = """{
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

_INVALID_JSON = """{
  "title": "BEST free shipping OBD2 scanner",
  "bullets": ["Only one bullet"],
  "search_terms": "",
  "description": ""
}"""


def _thread_config(thread_id: str) -> RunnableConfig:
    return cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})


def _mock_llm(content: str) -> AsyncMock:
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=content, model="test")
    return provider


@pytest.mark.asyncio
async def test_ms3_cli_e2e_auto_approve() -> None:
    graph = build_runner_graph()
    mock = _mock_llm(_VALID_JSON)
    with patch(_LLM_PATCH, return_value=mock):
        state = await run_listing_task(
            sku="X431",
            platform="amazon",
            product_info={"competitor_asins": ["B001"], "keywords": ["obd2"]},
            auto_approve=True,
            graph=graph,
        )

    assert state["status"] == TaskStatus.COMPLETED
    final_output = state.get("final_output")
    assert isinstance(final_output, dict)
    assert final_output.get("title")
    assert len(cast(list[str], final_output.get("bullets", []))) == 5


@pytest.mark.asyncio
async def test_ms3_cli_pauses_at_hitl() -> None:
    graph = build_runner_graph()
    mock = _mock_llm(_VALID_JSON)
    with patch(_LLM_PATCH, return_value=mock):
        state = await run_listing_task(
            sku="X431",
            platform="amazon",
            product_info={"competitor_asins": ["B001"]},
            auto_approve=False,
            graph=graph,
        )

    assert is_waiting_hitl(graph, state["task_id"])
    payload = serialize_run_result(state, waiting_hitl=True)
    assert payload["status"] == TaskStatus.WAITING_HITL.value
    assert payload["waiting_hitl"] is True


@pytest.mark.asyncio
async def test_ms3_hitl_approve_completes() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    mock = _mock_llm(_VALID_JSON)
    with patch(_LLM_PATCH, return_value=mock):
        await run_listing_task(
            sku="X431",
            platform="amazon",
            product_info={"competitor_asins": ["B001"]},
            task_id="ms3-hitl",
            graph=graph,
        )
        completed = await approve_hitl(graph, "ms3-hitl")

    assert completed["status"] == TaskStatus.COMPLETED
    assert completed.get("final_output") is not None


@pytest.mark.asyncio
async def test_ms3_degraded_research_still_completes() -> None:
    graph = build_runner_graph()
    mock = _mock_llm(_VALID_JSON)
    with (
        patch(
            "aeo_orchestrator.nodes.research._expand_keywords_with_llm",
            new_callable=AsyncMock,
            return_value=["obd2", "scanner"],
        ),
        patch(_LLM_PATCH, return_value=mock),
    ):
        state = await run_listing_task(
            sku="X431",
            platform="amazon",
            product_info={},
            auto_approve=True,
            graph=graph,
        )

    assert state.get("degraded_mode") is True
    assert state["status"] == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_ms3_compliance_retries_then_hitl() -> None:
    graph = build_graph(checkpointer=MemorySaver())
    state = initial_state(task_id="ms3-retry", platform="amazon", sku="X431")
    config = _thread_config("ms3-retry")
    provider = _mock_llm(_INVALID_JSON)

    call_count = 0

    async def alternating_llm(*_args: object, **_kwargs: object) -> LLMResponse:
        nonlocal call_count
        call_count += 1
        if call_count <= MAX_COMPLIANCE_RETRIES:
            return LLMResponse(content=_INVALID_JSON, model="test")
        return LLMResponse(content=_VALID_JSON, model="test")

    provider.chat.side_effect = alternating_llm

    with patch(_LLM_PATCH, return_value=provider):
        result = await graph.ainvoke(state, config=config)

    assert int(result.get("retry_count", 0)) >= MAX_COMPLIANCE_RETRIES
    compliance = result.get("compliance")
    assert isinstance(compliance, dict)
    assert compliance.get("passed") is False
    assert graph.get_state(config).next == ("human_review",)


def test_ms3_trace_queryable() -> None:
    runner = CliRunner()
    mock = _mock_llm(_VALID_JSON)
    with patch(_LLM_PATCH, return_value=mock):
        result = runner.invoke(
            main,
            [
                "run",
                "--sku",
                "X431",
                "--competitor",
                "B001",
                "--auto-approve",
                "--json",
            ],
        )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    trace = payload.get("trace")
    assert isinstance(trace, list)
    agents = {event["agent"] for event in trace if isinstance(event, dict)}
    assert "research_agent" in agents
    assert "rules_agent" in agents
    assert "generate_agent" in agents
    assert "compliance_agent" in agents
    assert payload["status"] == TaskStatus.COMPLETED.value
