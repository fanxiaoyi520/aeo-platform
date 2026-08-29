from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.nodes.generate import generate_node
from aeo_orchestrator.state import initial_state

_SAMPLE_JSON = """{
  "title": "LAUNCH X431 OBD2 Scanner Diagnostic Tool",
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


@pytest.mark.asyncio
async def test_generate_node_parses_llm_json() -> None:
    state = initial_state(
        task_id="g1",
        platform="amazon",
        sku="X431",
        product_info={"category": "OBD2 scanner"},
    )
    state["research"] = {"keywords": ["obd2"]}
    state["rules"] = {"rule_summary": "Title max 200 chars", "references": []}

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_JSON, model="test")

    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider):
        result = await generate_node(state)

    generated = result["generated"]
    assert isinstance(generated, dict)
    assert generated["title"].startswith("LAUNCH X431")
    assert len(generated["bullets"]) == 5
    assert generated["search_terms"] == "obd2 scanner diagnostic x431"


@pytest.mark.asyncio
async def test_generate_node_records_failure() -> None:
    state = initial_state(task_id="g2", platform="tiktok", sku="CRP123")
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = RuntimeError("llm timeout")

    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider):
        result = await generate_node(state)

    generated = result["generated"]
    assert isinstance(generated, dict)
    assert generated["error"] == "llm timeout"
    trace = result["trace"]
    assert isinstance(trace, list)
    assert trace[-1]["status"] == "failed"
