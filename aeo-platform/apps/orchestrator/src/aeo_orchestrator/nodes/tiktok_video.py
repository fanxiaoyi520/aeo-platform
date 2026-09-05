"""tiktok_video_agent — MV2-05: TikTok short video script + storyboard."""

from __future__ import annotations

import json
from typing import Any

from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event

_SYSTEM = """You are a TikTok Shop short video scriptwriter for automotive tools.
Return ONLY valid JSON with keys:
- script (object):
  - hook (string, ≤20 chars — attention-grabbing opening line)
  - selling_points (array of exactly 3 strings, each ≤15 chars — key product benefits)
  - cta (string — call-to-action phrase)
  - duration_seconds (integer — target video duration: 15, 30, or 60)
- storyboard (array of 3 to 5 objects):
  - shot (integer — shot number starting from 1)
  - visual (string, ≤40 chars — what the camera shows)
  - duration (string — e.g. "5s", "10s")
  - subtitle (string — on-screen text overlay)
  - bgm_mood (string — one word: energetic, relaxed, funny, dramatic, trendy)
Keep it trendy, short, and punchy. No markdown fences."""


def _build_user_prompt(state: TaskState) -> str:
    product_info = state.get("product_info") or {}
    generated = state.get("generated") or {}
    research = state.get("research") or {}
    image_copy = state.get("image_copy") or {}
    sections = [
        f"SKU: {state.get('sku', '')}",
        f"Market: {state.get('market', 'US')}",
        f"Product info: {json.dumps(product_info, ensure_ascii=False)}",
        f"Listing title: {generated.get('title', '')}",
        f"Listing bullets: {json.dumps(generated.get('bullets', []), ensure_ascii=False)}",
        f"Research: {json.dumps(research, ensure_ascii=False)}",
        f"Image copy: {json.dumps(image_copy, ensure_ascii=False)}",
    ]
    return "\n\n".join(sections)


def _parse_llm_json(text: str) -> dict[str, Any]:
    content = text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("LLM output must be a JSON object")
    return parsed


def _normalize_selling_points(raw: Any) -> list[str]:
    items: list[str] = []
    if isinstance(raw, list):
        items = [str(item).strip()[:15] for item in raw if item]
    while len(items) < 3:
        items.append("")
    return items[:3]


def _normalize_script(raw: Any) -> dict[str, object]:
    if not isinstance(raw, dict):
        raw = {}
    hook = str(raw.get("hook", "")).strip()[:20]
    valid_durations = {15, 30, 60}
    dur = raw.get("duration_seconds", 30)
    if not isinstance(dur, int) or dur not in valid_durations:
        dur = 30
    return {
        "hook": hook,
        "selling_points": _normalize_selling_points(raw.get("selling_points")),
        "cta": str(raw.get("cta", "")).strip(),
        "duration_seconds": dur,
    }


def _normalize_storyboard_shot(raw: Any, shot_num: int) -> dict[str, object]:
    if not isinstance(raw, dict):
        raw = {}
    visual = str(raw.get("visual", "")).strip()[:40]
    duration = str(raw.get("duration", "")).strip()
    valid_moods = {"energetic", "relaxed", "funny", "dramatic", "trendy"}
    bgm = str(raw.get("bgm_mood", "")).strip().lower()
    if bgm not in valid_moods:
        bgm = "trendy"
    return {
        "shot": shot_num,
        "visual": visual,
        "duration": duration,
        "subtitle": str(raw.get("subtitle", "")).strip(),
        "bgm_mood": bgm,
    }


def _normalize_storyboard(raw: Any) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    if isinstance(raw, list):
        for i, item in enumerate(raw[:5], start=1):
            items.append(_normalize_storyboard_shot(item, i))
    while len(items) < 3:
        items.append(_normalize_storyboard_shot(None, len(items) + 1))
    return items[:5]


def _normalize_generated(raw: dict[str, Any]) -> dict[str, object]:
    return {
        "script": _normalize_script(raw.get("script")),
        "storyboard": _normalize_storyboard(raw.get("storyboard")),
        "platform": "tiktok",
    }


def _empty_generated(*, error: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "script": _normalize_script(None),
        "storyboard": _normalize_storyboard(None),
        "platform": "tiktok",
    }
    if error:
        payload["error"] = error
    return payload


async def tiktok_video_node(state: TaskState) -> dict[str, object]:
    """tiktok_video_agent — produces TikTok short video script + storyboard via LLM."""
    trace = [with_started_trace(state, "tiktok_video_agent")]

    try:
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(role="system", content=_SYSTEM),
                Message(role="user", content=_build_user_prompt(state)),
            ],
            temperature=0.6,
        )
        generated = _normalize_generated(_parse_llm_json(response.content))
        script = generated["script"]
        storyboard = generated["storyboard"]
        trace.append(
            make_trace_event(
                "tiktok_video_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "selling_point_count": (
                        len(script["selling_points"]) if isinstance(script, dict) else 0
                    ),
                    "shot_count": len(storyboard) if isinstance(storyboard, list) else 0,
                },
            )
        )
    except Exception as exc:
        generated = _empty_generated(error=str(exc))
        trace.append(
            make_trace_event(
                "tiktok_video_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"tiktok_video": generated, "trace": trace}
