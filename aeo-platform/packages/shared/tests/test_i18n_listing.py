"""P7-20: Tests for multi-language listing generator."""

from __future__ import annotations

import pytest
from aeo_shared.i18n_listing import (
    GeneratedListing,
    ListingTemplate,
    LocaleLimits,
    effective_length,
    generate_listing,
    get_template,
)


class TestEffectiveLength:
    def test_ascii_counts_as_one(self) -> None:
        assert effective_length("hello") == 5

    def test_cjk_characters_count_as_two(self) -> None:
        # 3 CJK characters → 6
        assert effective_length("日本語") == 6

    def test_mixed_counts_correctly(self) -> None:
        # "hi" (2) + "日" (2) → 4
        assert effective_length("hi日") == 4

    def test_cjk_double_disabled(self) -> None:
        assert effective_length("日本語", cjk_double=False) == 3

    def test_hangul_counts_as_two(self) -> None:
        assert effective_length("한글") == 4

    def test_hiragana_katakana_count_as_two(self) -> None:
        assert effective_length("ひらがなカタカナ") == 16

    def test_empty_string(self) -> None:
        assert effective_length("") == 0


class TestGenerateListing:
    def test_english_listing(self) -> None:
        template = get_template("en")
        variables = {
            "product_name": "Widget Pro",
            "key_feature": "Durable titanium build",
            "benefit_1": "Lightweight",
            "benefit_2": "Rust-proof",
            "benefit_3": "Lifetime warranty",
            "use_case": "daily carry",
        }
        listing = generate_listing(template, variables)
        assert listing.locale == "en"
        assert "Widget Pro" in listing.title
        assert len(listing.bullet_points) == 3
        assert "Lightweight" in listing.bullet_points[0]
        assert "daily carry" in listing.description
        assert listing.truncated is False

    def test_german_listing(self) -> None:
        template = get_template("de")
        variables = {
            "product_name": "Widget Pro",
            "key_feature": "Robuster Titanbau",
            "benefit_1": "Leicht",
            "benefit_2": "Rostfrei",
            "benefit_3": "Lebenslange Garantie",
            "use_case": "den täglichen Gebrauch",
        }
        listing = generate_listing(template, variables)
        assert listing.locale == "de"
        assert "Leicht" in listing.bullet_points[0]
        assert "täglichen Gebrauch" in listing.description

    def test_japanese_listing(self) -> None:
        template = get_template("ja")
        variables = {
            "product_name": "ウィジェットプロ",
            "key_feature": "チタン製",
            "benefit_1": "軽量",
            "benefit_2": "サビない",
            "benefit_3": "永久保証",
            "use_case": "日常携行",
        }
        listing = generate_listing(template, variables)
        assert listing.locale == "ja"
        assert "軽量" in listing.bullet_points[0]
        # CJK characters count double
        assert listing.title_length >= len("ウィジェットプロ")

    def test_spanish_listing(self) -> None:
        template = get_template("es")
        variables = {
            "product_name": "Widget Pro",
            "key_feature": "Construcción de titanio",
            "benefit_1": "Ligero",
            "benefit_2": "Resistente al óxido",
            "benefit_3": "Garantía de por vida",
            "use_case": "uso diario",
        }
        listing = generate_listing(template, variables)
        assert listing.locale == "es"
        assert "Ligero" in listing.bullet_points[0]
        assert "uso diario" in listing.description

    def test_truncation_when_title_exceeds_limit(self) -> None:
        template = ListingTemplate(
            locale="en",
            title_template="{product_name}",
            bullet_templates=[],
            description_template="",
            limits=LocaleLimits(title=10, bullet_points=100, description=100),
        )
        listing = generate_listing(
            template, {"product_name": "A very long product name that exceeds"}
        )
        assert listing.title_length <= 10
        assert listing.truncated is True

    def test_truncation_respects_cjk_weight(self) -> None:
        template = ListingTemplate(
            locale="ja",
            title_template="{product_name}",
            bullet_templates=[],
            description_template="",
            limits=LocaleLimits(title=6, bullet_points=100, description=100),
        )
        # 4 CJK chars = 8 weight, limit = 6 → truncated to 3 chars (weight 6)
        listing = generate_listing(
            template, {"product_name": "日本語テスト"}
        )
        assert listing.title_length <= 6
        assert listing.truncated is True

    def test_no_truncation_when_within_limit(self) -> None:
        template = get_template("en")
        variables = {
            "product_name": "Widget",
            "key_feature": "Fast",
            "benefit_1": "A",
            "benefit_2": "B",
            "benefit_3": "C",
            "use_case": "home",
        }
        listing = generate_listing(template, variables)
        assert listing.truncated is False


class TestGetTemplate:
    def test_supported_locales(self) -> None:
        for locale in ("en", "de", "ja", "es"):
            template = get_template(locale)
            assert template.locale == locale

    def test_unsupported_locale_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported locale"):
            get_template("fr")  # type: ignore[arg-type]


class TestGeneratedListing:
    def test_is_dataclass(self) -> None:
        template = get_template("en")
        variables = {
            "product_name": "X",
            "key_feature": "Y",
            "benefit_1": "A",
            "benefit_2": "B",
            "benefit_3": "C",
            "use_case": "Z",
        }
        listing = generate_listing(template, variables)
        assert isinstance(listing, GeneratedListing)
        assert listing.title_length > 0
        assert listing.description_length > 0
