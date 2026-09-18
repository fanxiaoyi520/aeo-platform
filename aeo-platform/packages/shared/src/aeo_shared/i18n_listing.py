"""P7-20: Multi-language listing generator.

Supports EN / DE / JA / ES with locale-specific character limits and
templates. CJK characters count as double toward the limit (Amazon
and many marketplaces count bytes, not code points).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Locale = Literal["en", "de", "ja", "es"]

SUPPORTED_LOCALES: tuple[Locale, ...] = ("en", "de", "ja", "es")


@dataclass(frozen=True)
class LocaleLimits:
    """Per-locale character limits (bytes/code-points depending on field)."""

    title: int = 200
    bullet_points: int = 500
    description: int = 2000


@dataclass(frozen=True)
class ListingTemplate:
    """Locale-specific listing template with placeholders."""

    locale: Locale
    title_template: str
    bullet_templates: list[str]
    description_template: str
    limits: LocaleLimits = field(default_factory=LocaleLimits)


@dataclass(frozen=True)
class GeneratedListing:
    """Output of the listing generator."""

    locale: Locale
    title: str
    bullet_points: list[str]
    description: str
    title_length: int
    bullets_length: int
    description_length: int
    truncated: bool = False


DEFAULT_TEMPLATES: dict[Locale, ListingTemplate] = {
    "en": ListingTemplate(
        locale="en",
        title_template="{product_name} — {key_feature}",
        bullet_templates=[
            "✅ {benefit_1}",
            "✅ {benefit_2}",
            "✅ {benefit_3}",
        ],
        description_template=(
            "Introducing {product_name}. {key_feature}. "
            "Perfect for {use_case}."
        ),
    ),
    "de": ListingTemplate(
        locale="de",
        title_template="{product_name} — {key_feature}",
        bullet_templates=[
            "✅ {benefit_1}",
            "✅ {benefit_2}",
            "✅ {benefit_3}",
        ],
        description_template=(
            "Einführung von {product_name}. {key_feature}. "
            "Perfekt für {use_case}."
        ),
    ),
    "ja": ListingTemplate(
        locale="ja",
        title_template="{product_name} — {key_feature}",
        bullet_templates=[
            "✅ {benefit_1}",
            "✅ {benefit_2}",
            "✅ {benefit_3}",
        ],
        description_template=(
            "{product_name}のご紹介。{key_feature}。"
            "{use_case}に最適です。"
        ),
    ),
    "es": ListingTemplate(
        locale="es",
        title_template="{product_name} — {key_feature}",
        bullet_templates=[
            "✅ {benefit_1}",
            "✅ {benefit_2}",
            "✅ {benefit_3}",
        ],
        description_template=(
            "Presentamos {product_name}. {key_feature}. "
            "Perfecto para {use_case}."
        ),
    ),
}


def effective_length(text: str, *, cjk_double: bool = True) -> int:
    """Count characters, treating CJK as double-width when requested."""
    if not cjk_double:
        return len(text)
    count = 0
    for char in text:
        code_point = ord(char)
        # CJK Unified Ideographs + Kana + Hangul + fullwidth forms
        is_cjk = (
            0x4E00 <= code_point <= 0x9FFF  # CJK Unified
            or 0x3400 <= code_point <= 0x4DBF  # CJK Extension A
            or 0x3040 <= code_point <= 0x30FF  # Hiragana + Katakana
            or 0xAC00 <= code_point <= 0xD7AF  # Hangul Syllables
            or 0xFF00 <= code_point <= 0xFFEF  # Fullwidth Forms
        )
        count += 2 if is_cjk else 1
    return count


def _truncate_to_limit(text: str, limit: int, *, cjk_double: bool) -> tuple[str, bool]:
    if effective_length(text, cjk_double=cjk_double) <= limit:
        return text, False
    truncated = []
    running = 0
    for char in text:
        code_point = ord(char)
        is_cjk = (
            0x4E00 <= code_point <= 0x9FFF
            or 0x3400 <= code_point <= 0x4DBF
            or 0x3040 <= code_point <= 0x30FF
            or 0xAC00 <= code_point <= 0xD7AF
            or 0xFF00 <= code_point <= 0xFFEF
        )
        weight = 2 if is_cjk else 1
        if running + weight > limit:
            break
        truncated.append(char)
        running += weight
    return "".join(truncated), True


def generate_listing(
    template: ListingTemplate,
    variables: dict[str, str],
    *,
    cjk_double: bool = True,
) -> GeneratedListing:
    """Render a listing from a template and variables.

    Truncates fields that exceed the locale's limits and flags the
    result as ``truncated``.
    """
    title = template.title_template.format(**variables)
    description = template.description_template.format(**variables)
    bullets = [b.format(**variables) for b in template.bullet_templates]

    title, t1 = _truncate_to_limit(title, template.limits.title, cjk_double=cjk_double)
    description, t2 = _truncate_to_limit(
        description, template.limits.description, cjk_double=cjk_double
    )
    truncated_bullets: list[str] = []
    any_bullet_truncated = False
    for bullet in bullets:
        rendered, was_truncated = _truncate_to_limit(
            bullet, template.limits.bullet_points, cjk_double=cjk_double
        )
        truncated_bullets.append(rendered)
        any_bullet_truncated = any_bullet_truncated or was_truncated

    return GeneratedListing(
        locale=template.locale,
        title=title,
        bullet_points=truncated_bullets,
        description=description,
        title_length=effective_length(title, cjk_double=cjk_double),
        bullets_length=max(
            (effective_length(b, cjk_double=cjk_double) for b in truncated_bullets),
            default=0,
        ),
        description_length=effective_length(description, cjk_double=cjk_double),
        truncated=t1 or t2 or any_bullet_truncated,
    )


def get_template(locale: Locale) -> ListingTemplate:
    if locale not in DEFAULT_TEMPLATES:
        msg = f"Unsupported locale: {locale}. Supported: {SUPPORTED_LOCALES}"
        raise ValueError(msg)
    return DEFAULT_TEMPLATES[locale]
