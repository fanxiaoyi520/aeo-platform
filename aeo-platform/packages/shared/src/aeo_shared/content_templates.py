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

_SHOPIFY_LISTING = ContentTemplate(
    content_type="listing",
    platform="shopify",
    system_prompt="""You are a Shopify DTC store listing copywriter.
Return ONLY valid JSON with keys:
- title (string, max 100 chars — concise and brand-forward)
- bullets (array of exactly 4 strings — benefit-focused)
- search_terms (string)
- description (string — brand storytelling paragraph)
Focus on brand voice and direct consumer appeal. No markdown fences.""",
    output_schema={
        "title": "string ≤100 chars",
        "bullets": "array[4]",
        "search_terms": "string",
        "description": "string",
    },
    constraints={"title_max_chars": 100, "bullet_count": 4, "style": "brand-forward"},
)

_SHOPIFY_LANDING_PAGE = ContentTemplate(
    content_type="landing_page",
    platform="shopify",
    system_prompt="""You are a Shopify DTC landing page copywriter.
Return ONLY valid JSON with keys:
- hero_headline (string, max 60 chars — attention-grabbing headline)
- subheadline (string, max 120 chars — supporting value proposition)
- cta_text (string — call-to-action button text)
- body_paragraph (string — 2-3 sentence product story)
- social_proof (string — testimonial or trust signal)
Keep it conversion-focused and brand-consistent. No markdown fences.""",
    output_schema={
        "hero_headline": "string ≤60 chars",
        "subheadline": "string ≤120 chars",
        "cta_text": "string",
        "body_paragraph": "string",
        "social_proof": "string",
    },
    constraints={
        "headline_max_chars": 60,
        "subheadline_max_chars": 120,
        "style": "conversion-focused",
    },
)

_SHOPIFY_EMAIL_CAMPAIGN = ContentTemplate(
    content_type="email_campaign",
    platform="shopify",
    system_prompt="""You are a Shopify DTC email marketing copywriter.
Return ONLY valid JSON with keys:
- subject (string, max 60 chars — email subject line)
- preview_text (string, max 100 chars — preview text shown in inbox)
- body (string — email body copy, 3-5 sentences)
- sequence (array of strings — email sequence stages,
  e.g. ["welcome", "abandoned_cart", "post_purchase"])
- cta_text (string — call-to-action text)
Write compelling, personalized email copy. No markdown fences.""",
    output_schema={
        "subject": "string ≤60 chars",
        "preview_text": "string ≤100 chars",
        "body": "string",
        "sequence": "array[string]",
        "cta_text": "string",
    },
    constraints={
        "subject_max_chars": 60,
        "preview_max_chars": 100,
        "style": "personalized and compelling",
    },
)

_SHOPIFY_SOCIAL_POST = ContentTemplate(
    content_type="social_post",
    platform="shopify",
    system_prompt="""You are a Shopify DTC social media copywriter.
Return ONLY valid JSON with keys:
- platform (string — "instagram", "facebook", or "twitter")
- caption (string, max 2200 chars for Instagram, 63206 for Facebook, 280 for Twitter)
- hashtags (array of strings — relevant hashtags, 5-15 for Instagram, 2-5 for others)
- cta (string — call-to-action for the post)
- image_suggestion (string — brief description of recommended image)
Adapt tone to the platform. No markdown fences.""",
    output_schema={
        "platform": "string",
        "caption": "string",
        "hashtags": "array[string]",
        "cta": "string",
        "image_suggestion": "string",
    },
    constraints={
        "style": "platform-adaptive",
        "instagram_hashtag_range": [5, 15],
        "other_hashtag_range": [2, 5],
    },
)

_BUILTIN_TEMPLATES: list[ContentTemplate] = [
    _AMAZON_LISTING,
    _TIKTOK_LISTING,
    _AMAZON_IMAGE_COPY,
    _TIKTOK_IMAGE_COPY,
    _TIKTOK_VIDEO,
    _SHOPIFY_LISTING,
    _SHOPIFY_LANDING_PAGE,
    _SHOPIFY_EMAIL_CAMPAIGN,
    _SHOPIFY_SOCIAL_POST,
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
