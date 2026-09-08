"""MV2-06: ContentTemplateLibrary — centralized multi-platform prompt templates."""

from __future__ import annotations

import pytest
from aeo_shared.content_templates import (
    ContentTemplate,
    ContentTemplateLibrary,
    get_content_template_library,
)


class TestContentTemplate:
    def test_create_template(self) -> None:
        tpl = ContentTemplate(
            content_type="listing",
            platform="amazon",
            system_prompt="You are an Amazon copywriter.",
            output_schema={"title": "string", "bullets": "array[5]"},
            constraints={"title_max_chars": 200},
        )
        assert tpl.content_type == "listing"
        assert tpl.platform == "amazon"
        assert "Amazon" in tpl.system_prompt
        assert tpl.output_schema["title"] == "string"
        assert tpl.constraints["title_max_chars"] == 200

    def test_template_equality(self) -> None:
        a = ContentTemplate(content_type="listing", platform="amazon", system_prompt="A")
        b = ContentTemplate(content_type="listing", platform="amazon", system_prompt="A")
        assert a == b

    def test_template_to_dict(self) -> None:
        tpl = ContentTemplate(
            content_type="listing",
            platform="tiktok",
            system_prompt="TikTok writer",
            output_schema={"title": "string"},
            constraints={"bullet_max_chars": 80},
        )
        d = tpl.to_dict()
        assert d["content_type"] == "listing"
        assert d["platform"] == "tiktok"
        assert d["system_prompt"] == "TikTok writer"
        assert d["output_schema"] == {"title": "string"}
        assert d["constraints"] == {"bullet_max_chars": 80}


class TestContentTemplateLibrary:
    def test_get_existing_template(self) -> None:
        lib = ContentTemplateLibrary()
        tpl = lib.get("listing", "amazon")
        assert tpl.content_type == "listing"
        assert tpl.platform == "amazon"
        assert "Amazon" in tpl.system_prompt

    def test_get_tiktok_listing(self) -> None:
        lib = ContentTemplateLibrary()
        tpl = lib.get("listing", "tiktok")
        assert tpl.platform == "tiktok"
        assert "TikTok" in tpl.system_prompt

    def test_get_image_copy_amazon(self) -> None:
        lib = ContentTemplateLibrary()
        tpl = lib.get("image_copy", "amazon")
        assert tpl.content_type == "image_copy"
        assert "image" in tpl.system_prompt.lower()

    def test_get_image_copy_tiktok(self) -> None:
        lib = ContentTemplateLibrary()
        tpl = lib.get("image_copy", "tiktok")
        assert tpl.platform == "tiktok"

    def test_get_tiktok_video(self) -> None:
        lib = ContentTemplateLibrary()
        tpl = lib.get("tiktok_video", "tiktok")
        assert tpl.content_type == "tiktok_video"
        assert "video" in tpl.system_prompt.lower() or "script" in tpl.system_prompt.lower()

    def test_get_unknown_content_type_raises(self) -> None:
        lib = ContentTemplateLibrary()
        with pytest.raises(KeyError, match="unknown"):
            lib.get("unknown_type", "amazon")

    def test_get_unknown_platform_raises(self) -> None:
        lib = ContentTemplateLibrary()
        with pytest.raises(KeyError, match="shopify"):
            lib.get("listing", "shopify")

    def test_filter_by_content_type(self) -> None:
        lib = ContentTemplateLibrary()
        results = lib.filter_by(content_type="listing")
        assert len(results) == 2
        platforms = {t.platform for t in results}
        assert platforms == {"amazon", "tiktok"}

    def test_filter_by_platform(self) -> None:
        lib = ContentTemplateLibrary()
        results = lib.filter_by(platform="tiktok")
        assert len(results) >= 3
        for tpl in results:
            assert tpl.platform == "tiktok"

    def test_filter_by_both(self) -> None:
        lib = ContentTemplateLibrary()
        results = lib.filter_by(content_type="image_copy", platform="amazon")
        assert len(results) == 1
        assert results[0].content_type == "image_copy"
        assert results[0].platform == "amazon"

    def test_filter_no_match_returns_empty(self) -> None:
        lib = ContentTemplateLibrary()
        results = lib.filter_by(content_type="nonexistent")
        assert results == []

    def test_list_all(self) -> None:
        lib = ContentTemplateLibrary()
        all_templates = lib.list_all()
        assert len(all_templates) == 5
        types = {t.content_type for t in all_templates}
        assert "listing" in types
        assert "image_copy" in types
        assert "tiktok_video" in types

    def test_list_content_types(self) -> None:
        lib = ContentTemplateLibrary()
        types = lib.list_content_types()
        assert "listing" in types
        assert "image_copy" in types
        assert "tiktok_video" in types

    def test_list_platforms(self) -> None:
        lib = ContentTemplateLibrary()
        platforms = lib.list_platforms()
        assert "amazon" in platforms
        assert "tiktok" in platforms


class TestGetContentTemplateLibrary:
    def test_returns_singleton(self) -> None:
        lib1 = get_content_template_library()
        lib2 = get_content_template_library()
        assert lib1 is lib2

    def test_singleton_has_all_templates(self) -> None:
        lib = get_content_template_library()
        assert len(lib.list_all()) == 5
