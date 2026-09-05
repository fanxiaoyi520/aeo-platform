"""image_copy_agent — MV2-04: main image + scene image copywriting."""

from __future__ import annotations

import json
from typing import Any

from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event

_AMAZON_SYSTEM = """You are an Amazon product image copywriter for automotive tools.
Return ONLY valid JSON with keys:
- main_image (object):
  - callouts (array of exactly 3 strings, each ≤10 chars — short punchy labels for the main image)
  - badge_text (string — promotional badge text)
  - compliance_note (string — disclaimer or compliance note)
- scene_images (array of exactly 3 objects):
  - scene (string — scene name)
  - description (string, ≤30 chars — what the scene shows)
  - lifestyle_copy (string — lifestyle marketing copy)
  - mood (string — one word mood descriptor)
Follow the product context. No markdown fences."""

_TIKTOK_SYSTEM = """You are a TikTok Shop product image copywriter for automotive tools.
Return ONLY valid JSON with keys:
- main_image (object):
  - callouts (array of exactly 3 strings, each ≤10 chars — trendy short labels)
  - badge_text (string — catchy badge text)
  - compliance_note (string — short disclaimer)
- scene_images (array of exactly 3 objects):
  - scene (string — trendy scene name)
  - description (string, ≤30 chars — what the scene shows)
  - lifestyle_copy (string — punchy lifestyle copy)
  - mood (string — one word mood)
Keep it trendy and short. No markdown fences."""


def _system_prompt(platform: str) -> str:
    return _TIKTOK_SYSTEM if platform == "tiktok" else _AMAZON_SYSTEM


def _build_user_prompt(state: TaskState) -> str:
    product_info = state.get("product_info") or {}
    generated = state.get("generated") or {}
    research = state.get("research") or {}
    sections = [
        f"SKU: {state.get('sku', '')}",
        f"Platform: {state.get('platform', '')}",
        f"Market: {state.get('market', 'US')}",
        f"Product info: {json.dumps(product_info, ensure_ascii=False)}",
        f"Listing title: {generated.get('title', '')}",
        f"Listing bullets: {json.dumps(generated.get('bullets', []), ensure_ascii=False)}",
        f"Research: {json.dumps(research, ensure_ascii=False)}",
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


def _normalize_callouts(raw: Any) -> list[str]:
    items: list[str] = []
    if isinstance(raw, list):
        items = [str(item).strip()[:10] for item in raw if item]
    while len(items) < 3:
        items.append("")
    return items[:3]


def _normalize_main_image(raw: Any) -> dict[str, object]:
    if not isinstance(raw, dict):
        raw = {}
    return {
        "callouts": _normalize_callouts(raw.get("callouts", [])),
        "badge_text": str(raw.get("badge_text", "")).strip(),
        "compliance_note": str(raw.get("compliance_note", "")).strip(),
    }


def _normalize_scene(raw: Any) -> dict[str, object]:
    if not isinstance(raw, dict):
        raw = {}
    desc = str(raw.get("description", "")).strip()
    if len(desc) > 30:
        desc = desc[:30]
    return {
        "scene": str(raw.get("scene", "")).strip(),
        "description": desc,
        "lifestyle_copy": str(raw.get("lifestyle_copy", "")).strip(),
        "mood": str(raw.get("mood", "")).strip(),
    }


def _normalize_scene_images(raw: Any) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    if isinstance(raw, list):
        items = [_normalize_scene(item) for item in raw]
    while len(items) < 3:
        items.append(_normalize_scene(None))
    return items[:3]


def _normalize_generated(raw: dict[str, Any], platform: str) -> dict[str, object]:
    return {
        "main_image": _normalize_main_image(raw.get("main_image")),
        "scene_images": _normalize_scene_images(raw.get("scene_images")),
        "platform": platform,
    }


def _empty_generated(platform: str, *, error: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "main_image": _normalize_main_image(None),
        "scene_images": _normalize_scene_images(None),
        "platform": platform,
    }
    if error:
        payload["error"] = error
    return payload


async def image_copy_node(state: TaskState) -> dict[str, object]:
    """image_copy_agent — produces main image + scene image copy via LLM."""
    trace = [with_started_trace(state, "image_copy_agent")]
    platform = state.get("platform", "amazon")

    try:
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(role="system", content=_system_prompt(platform)),
                Message(role="user", content=_build_user_prompt(state)),
            ],
            temperature=0.5,
        )
        generated = _normalize_generated(_parse_llm_json(response.content), platform)
        main = generated["main_image"]
        scenes = generated["scene_images"]
        trace.append(
            make_trace_event(
                "image_copy_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "callout_count": len(main["callouts"]) if isinstance(main, dict) else 0,
                    "scene_count": len(scenes) if isinstance(scenes, list) else 0,
                },
            )
        )
    except Exception as exc:
        generated = _empty_generated(platform, error=str(exc))
        trace.append(
            make_trace_event(
                "image_copy_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"image_copy": generated, "trace": trace}
