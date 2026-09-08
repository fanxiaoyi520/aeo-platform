"""MV2-08: MV2 production acceptance — 10 SKU selection-to-content end-to-end."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.runner import (
    run_selection_to_content_task,
    serialize_selection_to_content_result,
)

_LISTING_JSON = json.dumps(
    {
        "title": "Test Product Title",
        "bullets": ["B1", "B2", "B3", "B4", "B5"],
        "search_terms": "test keywords",
        "description": "Test description",
    }
)

_IMAGE_COPY_JSON = json.dumps(
    {
        "main_image": {
            "callouts": ["A", "B", "C"],
            "badge_text": "Badge",
            "compliance_note": "Note",
        },
        "scene_images": [
            {"scene": "S1", "description": "D1", "lifestyle_copy": "L1", "mood": "calm"},
            {"scene": "S2", "description": "D2", "lifestyle_copy": "L2", "mood": "bold"},
            {"scene": "S3", "description": "D3", "lifestyle_copy": "L3", "mood": "warm"},
        ],
    }
)

_TIKTOK_VIDEO_JSON = json.dumps(
    {
        "script": {
            "hook": "Hook!",
            "selling_points": ["P1", "P2", "P3"],
            "cta": "Buy now",
            "duration_seconds": 30,
        },
        "storyboard": [
            {
                "shot": 1,
                "visual": "V1",
                "duration": "5s",
                "subtitle": "Sub1",
                "bgm_mood": "energetic",
            },
            {
                "shot": 2,
                "visual": "V2",
                "duration": "10s",
                "subtitle": "Sub2",
                "bgm_mood": "trendy",
            },
            {
                "shot": 3,
                "visual": "V3",
                "duration": "5s",
                "subtitle": "Sub3",
                "bgm_mood": "relaxed",
            },
        ],
    }
)


def _mock_llm(call_count: list[int]) -> LLMResponse:
    idx = call_count[0]
    call_count[0] += 1
    responses = [_LISTING_JSON, _IMAGE_COPY_JSON, _TIKTOK_VIDEO_JSON]
    return LLMResponse(content=responses[idx % 3], model="test")


TEN_SKUS: list[dict[str, Any]] = [
    {"sku": f"MV2-SKU-{i:03d}", "product_info": {"category": "tools", "name": f"Product {i}"}}
    for i in range(1, 11)
]


@pytest.mark.asyncio
async def test_mv2_acceptance_10_skus_all_stages_complete() -> None:
    call_count = [0]
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = lambda messages, **kw: _mock_llm(call_count)

    results = []
    with (
        patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.image_copy.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.tiktok_video.get_llm_provider", return_value=mock_provider),
    ):
        for item in TEN_SKUS:
            state = await run_selection_to_content_task(
                sku=str(item["sku"]),
                platform="amazon",
                product_info=dict(item["product_info"]),
            )
            results.append(serialize_selection_to_content_result(state))

    assert len(results) == 10

    for result in results:
        assert result["stages_completed"] == ["selection", "listing", "image_copy", "tiktok_video"]
        assert result["selection"] is not None
        assert result["generated"] is not None
        assert result["image_copy"] is not None
        assert result["tiktok_video"] is not None


@pytest.mark.asyncio
async def test_mv2_acceptance_listing_output_schema() -> None:
    call_count = [0]
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = lambda messages, **kw: _mock_llm(call_count)

    with (
        patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.image_copy.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.tiktok_video.get_llm_provider", return_value=mock_provider),
    ):
        state = await run_selection_to_content_task(
            sku="SCHEMA-001",
            platform="amazon",
            product_info={"category": "tools"},
        )

    result = serialize_selection_to_content_result(state)
    generated = result["generated"]
    assert "title" in generated
    assert "bullets" in generated
    assert len(generated["bullets"]) == 5

    image_copy = result["image_copy"]
    assert "main_image" in image_copy
    assert "scene_images" in image_copy
    assert len(image_copy["scene_images"]) == 3

    tiktok = result["tiktok_video"]
    assert "script" in tiktok
    assert "storyboard" in tiktok
    assert len(tiktok["storyboard"]) >= 3


@pytest.mark.asyncio
async def test_mv2_acceptance_trace_covers_all_agents() -> None:
    call_count = [0]
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = lambda messages, **kw: _mock_llm(call_count)

    with (
        patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.image_copy.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.tiktok_video.get_llm_provider", return_value=mock_provider),
    ):
        state = await run_selection_to_content_task(
            sku="TRACE-001",
            platform="amazon",
            product_info={"category": "tools"},
        )

    trace = state.get("trace", [])
    agents = {e["agent"] for e in trace}
    assert "selection_agent" in agents
    assert "generate_agent" in agents
    assert "image_copy_agent" in agents
    assert "tiktok_video_agent" in agents
