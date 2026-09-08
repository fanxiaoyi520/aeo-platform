"""MV2-05: tiktok_video_node — TikTok short video script + storyboard."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.state import TaskState, initial_state

_SAMPLE_VIDEO_JSON = """{
  "script": {
    "hook": "你还在用普通工具？",
    "selling_points": ["防水设计", "蓝牙5.3", "36H续航"],
    "cta": "点击购物车下单"
  },
  "storyboard": [
    {
      "shot": 1,
      "visual": "手持产品特写",
      "duration": "5s",
      "subtitle": "你还在用普通工具？",
      "bgm_mood": "energetic"
    },
    {
      "shot": 2,
      "visual": "户外使用场景",
      "duration": "10s",
      "subtitle": "防水设计 无惧风雨",
      "bgm_mood": "trendy"
    },
    {
      "shot": 3,
      "visual": "对比竞品画面",
      "duration": "10s",
      "subtitle": "蓝牙5.3 秒连不断",
      "bgm_mood": "dramatic"
    },
    {
      "shot": 4,
      "visual": "购物车动画",
      "duration": "5s",
      "subtitle": "点击购物车下单",
      "bgm_mood": "energetic"
    }
  ]
}"""


def _make_state(**overrides: Any) -> TaskState:
    base = initial_state(
        task_id=overrides.pop("task_id", "tv1"),
        platform=overrides.pop("platform", "tiktok"),
        sku=overrides.pop("sku", "TV-001"),
        product_info=overrides.pop("product_info", {"category": "tool"}),
    )
    for k, v in overrides.items():
        base[k] = v  # type: ignore[literal-required]
    return base


@pytest.mark.asyncio
async def test_tiktok_video_node_parses_llm_json() -> None:
    """tiktok_video_node should parse LLM JSON into structured output."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(
        generated={"title": "Pro Tool", "bullets": ["防水", "蓝牙"]},
        research={"keywords": ["tool"]},
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_VIDEO_JSON, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    assert isinstance(video, dict)

    script = video["script"]
    assert isinstance(script, dict)
    assert len(script["selling_points"]) == 3
    assert script["hook"]
    assert script["cta"]

    storyboard = video["storyboard"]
    assert isinstance(storyboard, list)
    assert len(storyboard) == 4
    for shot in storyboard:
        assert shot["shot"] >= 1
        assert shot["visual"]
        assert shot["duration"]
        assert shot["subtitle"]
        assert shot["bgm_mood"] in {"energetic", "relaxed", "funny", "dramatic", "trendy"}

    assert video["platform"] == "tiktok"


@pytest.mark.asyncio
async def test_tiktok_video_node_records_failure() -> None:
    """LLM failure should produce empty structure with error field."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv2")

    mock_provider = AsyncMock()
    mock_provider.chat.side_effect = RuntimeError("LLM down")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    assert "error" in video
    assert video["platform"] == "tiktok"
    assert isinstance(video["script"], dict)
    assert isinstance(video["storyboard"], list)
    assert len(video["storyboard"]) >= 3


@pytest.mark.asyncio
async def test_tiktok_video_node_normalizes_missing_fields() -> None:
    """Missing fields should be normalized to defaults."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv3")

    incomplete_json = '{"script": {"hook": "测试"}}'
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=incomplete_json, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    script = video["script"]
    assert len(script["selling_points"]) == 3
    assert script["cta"] == ""
    assert script["duration_seconds"] == 30

    storyboard = video["storyboard"]
    assert len(storyboard) == 3
    for shot in storyboard:
        assert shot["bgm_mood"] == "trendy"


@pytest.mark.asyncio
async def test_tiktok_video_node_truncates_long_strings() -> None:
    """Long strings should be truncated to schema limits."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv4")

    long_json = """{
      "script": {
        "hook": "这是一个超过二十个字符的非常长的开场白文字内容",
        "selling_points": ["短", "短", "短"],
        "cta": "下单",
        "duration_seconds": 30
      },
      "storyboard": [
        {
          "shot": 1,
          "visual": "这是一个超过四十个字符的非常长的画面描述内容测试文字",
          "duration": "5s",
          "subtitle": "字幕",
          "bgm_mood": "funny"
        },
        {"shot": 2, "visual": "画面", "duration": "5s", "subtitle": "字幕", "bgm_mood": "funny"},
        {"shot": 3, "visual": "画面", "duration": "5s", "subtitle": "字幕", "bgm_mood": "funny"}
      ]
    }"""
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=long_json, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    assert len(video["script"]["hook"]) <= 20
    for shot in video["storyboard"]:
        assert len(shot["visual"]) <= 40


@pytest.mark.asyncio
async def test_tiktok_video_node_invalid_duration_defaults_30() -> None:
    """Invalid duration_seconds should default to 30."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv5")

    bad_dur_json = """{
      "script": {
        "hook": "测试", "selling_points": ["a","b","c"],
        "cta": "下单", "duration_seconds": 99
      },
      "storyboard": [
        {"shot":1,"visual":"画面","duration":"5s","subtitle":"字幕","bgm_mood":"trendy"},
        {"shot":2,"visual":"画面","duration":"5s","subtitle":"字幕","bgm_mood":"trendy"},
        {"shot":3,"visual":"画面","duration":"5s","subtitle":"字幕","bgm_mood":"trendy"}
      ]
    }"""
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=bad_dur_json, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    assert video["script"]["duration_seconds"] == 30


@pytest.mark.asyncio
async def test_tiktok_video_node_invalid_bgm_mood_defaults_trendy() -> None:
    """Invalid bgm_mood should default to 'trendy'."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv6")

    bad_mood_json = """{
      "script": {
        "hook": "测试", "selling_points": ["a","b","c"],
        "cta": "下单", "duration_seconds": 15
      },
      "storyboard": [
        {"shot":1,"visual":"画面","duration":"5s","subtitle":"字幕","bgm_mood":"x"},
        {"shot":2,"visual":"画面","duration":"5s","subtitle":"字幕","bgm_mood":"energetic"},
        {"shot":3,"visual":"画面","duration":"5s","subtitle":"字幕","bgm_mood":"relaxed"}
      ]
    }"""
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=bad_mood_json, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    storyboard = video["storyboard"]
    assert storyboard[0]["bgm_mood"] == "trendy"
    assert storyboard[1]["bgm_mood"] == "energetic"
    assert storyboard[2]["bgm_mood"] == "relaxed"


@pytest.mark.asyncio
async def test_tiktok_video_node_strips_markdown_fences() -> None:
    """LLM output wrapped in markdown fences should be parsed correctly."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv7")

    fenced_json = f"```json\n{_SAMPLE_VIDEO_JSON}\n```"
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=fenced_json, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    assert video["script"]["hook"] == "你还在用普通工具？"


@pytest.mark.asyncio
async def test_tiktok_video_node_trace_events() -> None:
    """Successful run should produce started + completed trace events."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv8")

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=_SAMPLE_VIDEO_JSON, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    trace = cast("list[Any]", result["trace"])
    assert len(trace) == 2
    assert trace[0]["status"] == "started"
    assert trace[0]["agent"] == "tiktok_video_agent"
    assert trace[1]["status"] == "completed"
    assert trace[1]["agent"] == "tiktok_video_agent"


@pytest.mark.asyncio
async def test_tiktok_video_node_storyboard_max_5_shots() -> None:
    """Storyboard should be capped at 5 shots even if LLM returns more."""
    from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node

    state = _make_state(task_id="tv9")

    six_shots = """{
      "script": {
        "hook": "测试", "selling_points": ["a","b","c"],
        "cta": "下单", "duration_seconds": 60
      },
      "storyboard": [
        {"shot":1,"visual":"画面1","duration":"5s","subtitle":"字幕1","bgm_mood":"trendy"},
        {"shot":2,"visual":"画面2","duration":"5s","subtitle":"字幕2","bgm_mood":"trendy"},
        {"shot":3,"visual":"画面3","duration":"5s","subtitle":"字幕3","bgm_mood":"trendy"},
        {"shot":4,"visual":"画面4","duration":"5s","subtitle":"字幕4","bgm_mood":"trendy"},
        {"shot":5,"visual":"画面5","duration":"5s","subtitle":"字幕5","bgm_mood":"trendy"},
        {"shot":6,"visual":"画面6","duration":"5s","subtitle":"字幕6","bgm_mood":"trendy"}
      ]
    }"""
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=six_shots, model="test")

    with patch(
        "aeo_orchestrator.nodes.tiktok_video.get_llm_provider",
        return_value=mock_provider,
    ):
        result = await tiktok_video_node(state)

    video = cast("dict[str, Any]", result["tiktok_video"])
    assert len(video["storyboard"]) == 5
