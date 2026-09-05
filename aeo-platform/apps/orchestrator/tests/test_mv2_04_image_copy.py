"""MV2-04: image_copy_node — main image + scene image copywriting."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.state import initial_state

_SAMPLE_MAIN_IMAGE_JSON = """{
  "main_image": {
    "callouts": ["防水", "蓝牙5.3", "降噪"],
    "badge_text": "热销爆款",
    "compliance_note": "结果因使用环境而异"
  },
  "scene_images": [
    {
      "scene": "通勤路上",
      "description": "地铁上享受安静音乐",
      "lifestyle_copy": "通勤也能很享受",
      "mood": "relaxed"
    },
    {
      "scene": "办公室",
      "description": "开放式办公专注利器",
      "lifestyle_copy": "效率翻倍不是梦",
      "mood": "focused"
    },
    {
      "scene": "健身房",
      "description": "运动不怕汗渍水渍",
      "lifestyle_copy": "运动好搭档",
      "mood": "energetic"
    }
  ]
}"""


@pytest.mark.asyncio
async def test_image_copy_node_parses_llm_json() -> None:
    """image_copy_node should parse LLM JSON into structured output."""
    from aeo_orchestrator.nodes.image_copy import image_copy_node

    state = initial_state(
        task_id="ic1",
        platform="amazon",
        sku="IMG-001",
        product_info={"category": "wireless earbuds", "name": "Acme Pro"},
    )
    state["research"] = {"keywords": ["wireless earbuds"]}
    state["generated"] = {
        "title": "Acme Wireless Earbuds Pro",
        "bullets": ["ANC", "BT5.3", "32H", "IPX5", "Comfort"],
    }

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_MAIN_IMAGE_JSON, model="test")

    with patch(
        "aeo_orchestrator.nodes.image_copy.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await image_copy_node(state)

    image_copy = result["image_copy"]
    assert isinstance(image_copy, dict)

    main = image_copy["main_image"]
    assert isinstance(main, dict)
    assert len(main["callouts"]) == 3
    assert all(len(c) <= 10 for c in main["callouts"])
    assert main["badge_text"]
    assert main["compliance_note"]

    scenes = image_copy["scene_images"]
    assert isinstance(scenes, list)
    assert len(scenes) == 3
    for scene in scenes:
        assert scene["scene"]
        assert scene["description"]
        assert len(scene["description"]) <= 30
        assert scene["lifestyle_copy"]
        assert scene["mood"]


@pytest.mark.asyncio
async def test_image_copy_node_records_failure() -> None:
    """image_copy_node should record failure when LLM raises."""
    from aeo_orchestrator.nodes.image_copy import image_copy_node

    state = initial_state(task_id="ic2", platform="tiktok", sku="IMG-002")
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = RuntimeError("llm timeout")

    with patch(
        "aeo_orchestrator.nodes.image_copy.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await image_copy_node(state)

    image_copy = result["image_copy"]
    assert isinstance(image_copy, dict)
    assert image_copy["error"] == "llm timeout"

    trace = result["trace"]
    assert isinstance(trace, list)
    assert trace[-1]["status"] == "failed"


@pytest.mark.asyncio
async def test_image_copy_node_amazon_system_prompt() -> None:
    """Amazon platform should use Amazon-specific system prompt."""
    from aeo_orchestrator.nodes.image_copy import image_copy_node

    state = initial_state(
        task_id="ic3",
        platform="amazon",
        sku="IMG-003",
        product_info={"category": "tool"},
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_MAIN_IMAGE_JSON, model="test")

    with patch(
        "aeo_orchestrator.nodes.image_copy.get_llm_provider",
        return_value=mock_provider,
    ):
        await image_copy_node(state)

    call_args = mock_provider.chat.call_args
    messages = call_args[0][0]
    system_msg = messages[0]
    assert "Amazon" in system_msg.content or "amazon" in system_msg.content.lower()


@pytest.mark.asyncio
async def test_image_copy_node_tiktok_system_prompt() -> None:
    """TikTok platform should use TikTok-specific system prompt."""
    from aeo_orchestrator.nodes.image_copy import image_copy_node

    state = initial_state(
        task_id="ic4",
        platform="tiktok",
        sku="IMG-004",
        product_info={"category": "tool"},
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_MAIN_IMAGE_JSON, model="test")

    with patch(
        "aeo_orchestrator.nodes.image_copy.get_llm_provider",
        return_value=mock_provider,
    ):
        await image_copy_node(state)

    call_args = mock_provider.chat.call_args
    messages = call_args[0][0]
    system_msg = messages[0]
    assert "TikTok" in system_msg.content or "tiktok" in system_msg.content.lower()


@pytest.mark.asyncio
async def test_image_copy_node_normalizes_missing_fields() -> None:
    """Missing fields should be normalized to defaults."""
    from aeo_orchestrator.nodes.image_copy import image_copy_node

    state = initial_state(
        task_id="ic5",
        platform="amazon",
        sku="IMG-005",
        product_info={"category": "tool"},
    )

    incomplete_json = '{"main_image": {"callouts": ["A"]}}'
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=incomplete_json, model="test")

    with patch(
        "aeo_orchestrator.nodes.image_copy.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await image_copy_node(state)

    image_copy = cast("dict[str, Any]", result["image_copy"])
    main = image_copy["main_image"]
    assert len(main["callouts"]) == 3
    assert main["badge_text"] == ""
    assert main["compliance_note"] == ""

    scenes = image_copy["scene_images"]
    assert len(scenes) == 3
    for scene in scenes:
        assert scene["scene"] == ""
        assert scene["description"] == ""
        assert scene["lifestyle_copy"] == ""
        assert scene["mood"] == ""


@pytest.mark.asyncio
async def test_image_copy_node_strips_markdown_fences() -> None:
    """LLM output wrapped in markdown fences should be parsed correctly."""
    from aeo_orchestrator.nodes.image_copy import image_copy_node

    state = initial_state(
        task_id="ic6",
        platform="amazon",
        sku="IMG-006",
        product_info={"category": "tool"},
    )

    fenced_json = f"```json\n{_SAMPLE_MAIN_IMAGE_JSON}\n```"
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=fenced_json, model="test")

    with patch(
        "aeo_orchestrator.nodes.image_copy.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await image_copy_node(state)

    image_copy = cast("dict[str, Any]", result["image_copy"])
    assert image_copy["main_image"]["badge_text"] == "热销爆款"


@pytest.mark.asyncio
async def test_image_copy_node_trace_events() -> None:
    """Successful run should produce started + completed trace events."""
    from aeo_orchestrator.nodes.image_copy import image_copy_node

    state = initial_state(
        task_id="ic7",
        platform="amazon",
        sku="IMG-007",
        product_info={"category": "tool"},
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_MAIN_IMAGE_JSON, model="test")

    with patch(
        "aeo_orchestrator.nodes.image_copy.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await image_copy_node(state)

    trace = cast("list[Any]", result["trace"])
    assert len(trace) == 2
    assert trace[0]["status"] == "started"
    assert trace[0]["agent"] == "image_copy_agent"
    assert trace[1]["status"] == "completed"
    assert trace[1]["agent"] == "image_copy_agent"
