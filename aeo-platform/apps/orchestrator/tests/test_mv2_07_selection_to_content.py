"""MV2-07: Selection → Content AIGC automatic task chain."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.runner import (
    run_selection_to_content_task,
    serialize_selection_to_content_result,
)

_LISTING_JSON = json.dumps(
    {
        "title": "Acme OBD2 Scanner Pro",
        "bullets": [
            "READS ALL OBD2 CODES",
            "LIVE DATA STREAMING",
            "COMPACT DESIGN",
            "MULTI-VEHICLE COMPATIBLE",
            "EASY PLUG-AND-PLAY",
        ],
        "search_terms": "obd2 scanner diagnostic tool",
        "description": "Professional OBD2 scanner.",
    }
)

_IMAGE_COPY_JSON = json.dumps(
    {
        "main_image": {
            "callouts": ["Fast", "Accurate", "Compact"],
            "badge_text": "Best Seller",
            "compliance_note": "Results may vary",
        },
        "scene_images": [
            {
                "scene": "Garage",
                "description": "Mechanic using scanner",
                "lifestyle_copy": "Pro tools",
                "mood": "reliable",
            },
            {
                "scene": "Dashboard",
                "description": "Close-up of screen",
                "lifestyle_copy": "Clear data",
                "mood": "precise",
            },
            {
                "scene": "On-the-go",
                "description": "In car storage",
                "lifestyle_copy": "Take anywhere",
                "mood": "convenient",
            },
        ],
    }
)

_TIKTOK_VIDEO_JSON = json.dumps(
    {
        "script": {
            "hook": "Fix your car in seconds!",
            "selling_points": ["Reads all codes", "Live data", "Plug & play"],
            "cta": "Link in bio",
            "duration_seconds": 30,
        },
        "storyboard": [
            {
                "shot": 1,
                "visual": "Close-up scanner",
                "duration": "5s",
                "subtitle": "Check engine?",
                "bgm_mood": "energetic",
            },
            {
                "shot": 2,
                "visual": "Plug into OBD port",
                "duration": "5s",
                "subtitle": "Plug it in",
                "bgm_mood": "energetic",
            },
            {
                "shot": 3,
                "visual": "Screen shows codes",
                "duration": "10s",
                "subtitle": "Read codes fast",
                "bgm_mood": "trendy",
            },
        ],
    }
)


def _mock_llm_response(call_count: list[int]) -> LLMResponse:
    idx = call_count[0]
    call_count[0] += 1
    if idx == 0:
        return LLMResponse(content=_LISTING_JSON, model="test")
    if idx == 1:
        return LLMResponse(content=_IMAGE_COPY_JSON, model="test")
    return LLMResponse(content=_TIKTOK_VIDEO_JSON, model="test")


@pytest.mark.asyncio
async def test_pipeline_runs_all_four_stages() -> None:
    call_count = [0]
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = lambda messages, **kw: _mock_llm_response(call_count)

    product_info = {
        "category": "automotive tools",
        "name": "OBD2 Scanner",
        "price": 49.99,
        "competitors": [{"title": "Competitor A", "price": 59.99}],
    }

    with (
        patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.image_copy.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.tiktok_video.get_llm_provider", return_value=mock_provider),
    ):
        state = await run_selection_to_content_task(
            sku="TEST-001",
            platform="amazon",
            market="US",
            product_info=product_info,
        )

    assert state.get("selection") is not None
    assert state.get("generated") is not None
    assert state.get("image_copy") is not None
    assert state.get("tiktok_video") is not None


@pytest.mark.asyncio
async def test_pipeline_state_flows_between_stages() -> None:
    call_count = [0]
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = lambda messages, **kw: _mock_llm_response(call_count)

    product_info = {"category": "automotive tools", "name": "OBD2 Scanner"}

    with (
        patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.image_copy.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.tiktok_video.get_llm_provider", return_value=mock_provider),
    ):
        state = await run_selection_to_content_task(
            sku="TEST-002",
            platform="amazon",
            product_info=product_info,
        )

    generated = state.get("generated") or {}
    assert generated.get("title") == "Acme OBD2 Scanner Pro"
    assert len(generated.get("bullets", [])) == 5

    image_copy = state.get("image_copy") or {}
    assert "main_image" in image_copy

    tiktok_video = state.get("tiktok_video") or {}
    assert "script" in tiktok_video
    assert "storyboard" in tiktok_video


@pytest.mark.asyncio
async def test_pipeline_trace_accumulates() -> None:
    call_count = [0]
    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = lambda messages, **kw: _mock_llm_response(call_count)

    with (
        patch("aeo_orchestrator.nodes.generate.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.image_copy.get_llm_provider", return_value=mock_provider),
        patch("aeo_orchestrator.nodes.tiktok_video.get_llm_provider", return_value=mock_provider),
    ):
        state = await run_selection_to_content_task(
            sku="TEST-003",
            platform="amazon",
            product_info={"category": "tools"},
        )

    trace = state.get("trace", [])
    agents_in_trace = {event["agent"] for event in trace}
    assert "selection_agent" in agents_in_trace
    assert "generate_agent" in agents_in_trace
    assert "image_copy_agent" in agents_in_trace
    assert "tiktok_video_agent" in agents_in_trace


def test_serialize_selection_to_content_result() -> None:
    state = {
        "task_id": "t1",
        "sku": "SKU-001",
        "platform": "amazon",
        "market": "US",
        "selection": {"score": 85, "report": "Good product"},
        "generated": {"title": "Test Title", "bullets": ["a"] * 5},
        "image_copy": {"main_image": {"callouts": ["x", "y", "z"]}},
        "tiktok_video": {"script": {"hook": "Buy now"}},
        "trace": [],
    }
    result = serialize_selection_to_content_result(state)  # type: ignore[arg-type]
    assert result["task_id"] == "t1"
    assert result["sku"] == "SKU-001"
    assert result["selection"]["score"] == 85
    assert result["generated"]["title"] == "Test Title"
    assert "main_image" in result["image_copy"]
    assert result["tiktok_video"]["script"]["hook"] == "Buy now"
    assert result["stages_completed"] == ["selection", "listing", "image_copy", "tiktok_video"]
