from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.nodes.generate import generate_node
from aeo_orchestrator.state import initial_state

_SAMPLE_JSON = """{
  "title": "Acme Wireless Earbuds Pro Bluetooth 5.3 Noise Cancelling",
  "bullets": [
    "ACTIVE NOISE CANCELLING for commute and office use",
    "BLUETOOTH 5.3 with low latency game mode",
    "32H TOTAL PLAYTIME with compact charging case",
    "IPX5 WATER RESISTANT for workouts and daily use",
    "COMFORT FIT with three ear tip sizes included"
  ],
  "search_terms": "wireless earbuds bluetooth noise cancelling",
  "description": "Premium wireless earbuds with hybrid ANC."
}"""


@pytest.mark.asyncio
async def test_generate_node_parses_llm_json() -> None:
    state = initial_state(
        task_id="g1",
        platform="amazon",
        sku="DEMO-001",
        product_info={"category": "wireless earbuds"},
    )
    state["research"] = {"keywords": ["wireless earbuds"]}
    state["rules"] = {"rule_summary": "Title max 200 chars", "references": []}

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_JSON, model="test")

    with patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider):
        result = await generate_node(state)

    generated = result["generated"]
    assert isinstance(generated, dict)
    assert generated["title"].startswith("Acme Wireless")
    assert len(generated["bullets"]) == 5
    assert generated["search_terms"] == "wireless earbuds bluetooth noise cancelling"


@pytest.mark.asyncio
async def test_generate_node_records_failure() -> None:
    state = initial_state(task_id="g2", platform="tiktok", sku="DEMO-002")
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
