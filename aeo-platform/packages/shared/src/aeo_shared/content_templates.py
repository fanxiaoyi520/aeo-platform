"""MV2-06: Multi-platform content template library.

Centralizes system prompts and output schemas for all content generation
nodes (listing, image_copy, tiktok_video) across platforms (amazon, tiktok).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContentTemplate:
    """A platform-specific prompt template for a content type."""

    content_type: str
    platform: str
    system_prompt: str
    output_schema: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_type": self.content_type,
            "platform": self.platform,
            "system_prompt": self.system_prompt,
            "output_schema": self.output_schema,
            "constraints": self.constraints,
        }


_AMAZON_LISTING = ContentTemplate(
    content_type="listing",
    platform="amazon",
    system_prompt="""You are an Amazon listing copywriter for automotive diagnostic tools.
Return ONLY valid JSON with keys:
- title (string, max 200 chars)
- bullets (array of exactly 5 strings)
- search_terms (string)
- description (string, optional)
Follow the rules and research context. No markdown fences.""",
    output_schema={
        "title": "string",
        "bullets": "array[5]",
        "search_terms": "string",
        "description": "string (optional)",
    },
    constraints={"title_max_chars": 200, "bullet_count": 5},
)

_TIKTOK_LISTING = ContentTemplate(
    content_type="listing",
    platform="tiktok",
    system_prompt="""You are a TikTok Shop listing copywriter for automotive tools.
Return ONLY valid JSON with keys:
- title (string)
- bullets (array of exactly 5 short punchy strings)
- search_terms (string)
- description (string, optional)
Follow the rules and research context. No markdown fences.""",
    output_schema={
        "title": "string",
        "bullets": "array[5]",
        "search_terms": "string",
        "description": "string (optional)",
    },
    constraints={"bullet_count": 5, "style": "short punchy"},
)

_AMAZON_IMAGE_COPY = ContentTemplate(
    content_type="image_copy",
    platform="amazon",
    system_prompt="""You are an Amazon product image copywriter for automotive tools.
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
Follow the product context. No markdown fences.""",
    output_schema={
        "main_image": {
            "callouts": "array[3] ≤10 chars each",
            "badge_text": "string",
            "compliance_note": "string",
        },
        "scene_images": "array[3] of {scene, description ≤30 chars, lifestyle_copy, mood}",
    },
    constraints={
        "callout_max_chars": 10,
        "callout_count": 3,
        "scene_count": 3,
        "scene_desc_max_chars": 30,
    },
)

_TIKTOK_IMAGE_COPY = ContentTemplate(
    content_type="image_copy",
    platform="tiktok",
    system_prompt="""You are a TikTok Shop product image copywriter for automotive tools.
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
Keep it trendy and short. No markdown fences.""",
    output_schema={
        "main_image": {
            "callouts": "array[3] ≤10 chars each",
            "badge_text": "string",
            "compliance_note": "string",
        },
        "scene_images": "array[3] of {scene, description ≤30 chars, lifestyle_copy, mood}",
    },
    constraints={
        "callout_max_chars": 10,
        "callout_count": 3,
        "scene_count": 3,
        "scene_desc_max_chars": 30,
        "style": "trendy and short",
    },
)

_TIKTOK_VIDEO = ContentTemplate(
    content_type="tiktok_video",
    platform="tiktok",
    system_prompt="""You are a TikTok Shop short video scriptwriter for automotive tools.
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
Keep it trendy, short, and punchy. No markdown fences.""",
    output_schema={
        "script": {
            "hook": "string ≤20 chars",
            "selling_points": "array[3] ≤15 chars each",
            "cta": "string",
            "duration_seconds": "int ∈ {15, 30, 60}",
        },
        "storyboard": "array[3-5] of {shot, visual ≤40 chars, duration, subtitle, bgm_mood}",
    },
    constraints={
        "hook_max_chars": 20,
        "selling_point_count": 3,
        "selling_point_max_chars": 15,
        "valid_durations": [15, 30, 60],
        "storyboard_min": 3,
        "storyboard_max": 5,
        "visual_max_chars": 40,
        "valid_bgm_moods": ["energetic", "relaxed", "funny", "dramatic", "trendy"],
    },
)

_BUILTIN_TEMPLATES: list[ContentTemplate] = [
    _AMAZON_LISTING,
    _TIKTOK_LISTING,
    _AMAZON_IMAGE_COPY,
    _TIKTOK_IMAGE_COPY,
    _TIKTOK_VIDEO,
]


class ContentTemplateLibrary:
    """Registry of content templates indexed by (content_type, platform)."""

    def __init__(self, templates: list[ContentTemplate] | None = None) -> None:
        self._templates = templates if templates is not None else list(_BUILTIN_TEMPLATES)
        self._index: dict[tuple[str, str], ContentTemplate] = {
            (t.content_type, t.platform): t for t in self._templates
        }

    def get(self, content_type: str, platform: str) -> ContentTemplate:
        key = (content_type, platform)
        if key not in self._index:
            raise KeyError(
                f"Template not found: content_type={content_type!r}, platform={platform!r}"
            )
        return self._index[key]

    def filter_by(
        self,
        *,
        content_type: str | None = None,
        platform: str | None = None,
    ) -> list[ContentTemplate]:
        results = self._templates
        if content_type is not None:
            results = [t for t in results if t.content_type == content_type]
        if platform is not None:
            results = [t for t in results if t.platform == platform]
        return results

    def list_all(self) -> list[ContentTemplate]:
        return list(self._templates)

    def list_content_types(self) -> list[str]:
        return sorted({t.content_type for t in self._templates})

    def list_platforms(self) -> list[str]:
        return sorted({t.platform for t in self._templates})


_LIBRARY_INSTANCE: ContentTemplateLibrary | None = None


def get_content_template_library() -> ContentTemplateLibrary:
    """Return a shared singleton ContentTemplateLibrary."""
    global _LIBRARY_INSTANCE
    if _LIBRARY_INSTANCE is None:
        _LIBRARY_INSTANCE = ContentTemplateLibrary()
    return _LIBRARY_INSTANCE
