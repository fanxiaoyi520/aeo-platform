"""generate_agent — S3-04: LLM listing generation with platform templates."""

from __future__ import annotations

import json
from typing import Any

from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event

_AMAZON_SYSTEM = """You are an Amazon listing copywriter for automotive diagnostic tools.
Return ONLY valid JSON with keys:
- title (string, max 200 chars)
- bullets (array of exactly 5 strings)
- search_terms (string)
- description (string, optional)
Follow the rules and research context. No markdown fences."""

_TIKTOK_SYSTEM = """You are a TikTok Shop listing copywriter for automotive tools.
Return ONLY valid JSON with keys:
- title (string)
- bullets (array of exactly 5 short punchy strings)
- search_terms (string)
- description (string, optional)
Follow the rules and research context. No markdown fences."""


def _system_prompt(platform: str) -> str:
    return _TIKTOK_SYSTEM if platform == "tiktok" else _AMAZON_SYSTEM


def _build_user_prompt(state: TaskState) -> str:
    research = state.get("research") or {}
    rules = state.get("rules") or {}
    product_info = state.get("product_info") or {}
    sections = [
        f"SKU: {state.get('sku', '')}",
        f"Platform: {state.get('platform', '')}",
        f"Market: {state.get('market', 'US')}",
        f"Product info: {json.dumps(product_info, ensure_ascii=False)}",
        f"Research: {json.dumps(research, ensure_ascii=False)}",
        f"Rules summary: {rules.get('rule_summary', '')}",
    ]

    references = rules.get("references")
    if isinstance(references, list):
        snippets: list[str] = []
        for ref in references[:4]:
            if isinstance(ref, dict) and ref.get("content"):
                snippets.append(str(ref["content"])[:320])
        if snippets:
            sections.append("Reference snippets:\n" + "\n---\n".join(snippets))

    feedback = state.get("human_feedback")
    if isinstance(feedback, str) and feedback.strip():
        sections.append(f"Human revision feedback:\n{feedback.strip()}")

    compliance = state.get("compliance") or {}
    issues = compliance.get("issues")
    if isinstance(issues, list) and issues:
        sections.append(f"Fix these compliance issues:\n{json.dumps(issues, ensure_ascii=False)}")

    return "\n\n".join(sections)


def _parse_llm_json(text: str) -> dict[str, Any]:
    content = text.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("LLM output must be a JSON object")
    return parsed


def _normalize_generated(raw: dict[str, Any], platform: str) -> dict[str, object]:
    bullets_raw = raw.get("bullets", [])
    bullets: list[str] = []
    if isinstance(bullets_raw, list):
        bullets = [str(item).strip() for item in bullets_raw if item]
    while len(bullets) < 5:
        bullets.append("")
    bullets = bullets[:5]

    return {
        "title": str(raw.get("title", "")).strip(),
        "bullets": bullets,
        "search_terms": str(raw.get("search_terms", "")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "platform": platform,
    }


def _empty_generated(platform: str, *, error: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "",
        "bullets": [""] * 5,
        "search_terms": "",
        "description": "",
        "platform": platform,
    }
    if error:
        payload["error"] = error
    return payload


async def generate_node(state: TaskState) -> dict[str, object]:
    """generate_agent — produces platform listing draft via LLM."""
    trace = [with_started_trace(state, "generate_agent")]
    platform = state.get("platform", "amazon")

    try:
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(role="system", content=_system_prompt(platform)),
                Message(role="user", content=_build_user_prompt(state)),
            ],
            temperature=0.4,
        )
        generated = _normalize_generated(_parse_llm_json(response.content), platform)
        bullets = generated["bullets"]
        trace.append(
            make_trace_event(
                "generate_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "title_len": len(str(generated["title"])),
                    "bullet_count": len(bullets) if isinstance(bullets, list) else 0,
                },
            )
        )
    except Exception as exc:
        generated = _empty_generated(platform, error=str(exc))
        trace.append(
            make_trace_event(
                "generate_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"generated": generated, "trace": trace}
