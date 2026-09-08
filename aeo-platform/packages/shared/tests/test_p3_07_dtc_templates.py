"""P3-07 acceptance tests — DTC Content Templates."""

from __future__ import annotations


def test_shopify_listing_template_exists() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    template = lib.get("listing", "shopify")
    assert template.content_type == "listing"
    assert template.platform == "shopify"
    assert "brand" in template.system_prompt.lower()


def test_shopify_landing_page_template_exists() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    template = lib.get("landing_page", "shopify")
    assert template.content_type == "landing_page"
    assert template.platform == "shopify"
    assert "hero_headline" in template.output_schema


def test_shopify_email_campaign_template_exists() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    template = lib.get("email_campaign", "shopify")
    assert template.content_type == "email_campaign"
    assert template.platform == "shopify"
    assert "subject" in template.output_schema
    assert "sequence" in template.output_schema


def test_shopify_social_post_template_exists() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    template = lib.get("social_post", "shopify")
    assert template.content_type == "social_post"
    assert template.platform == "shopify"
    assert "hashtags" in template.output_schema


def test_shopify_templates_filter_by_platform() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    shopify_templates = lib.filter_by(platform="shopify")
    assert len(shopify_templates) >= 4

    content_types = {t.content_type for t in shopify_templates}
    assert "listing" in content_types
    assert "landing_page" in content_types
    assert "email_campaign" in content_types
    assert "social_post" in content_types


def test_shopify_in_list_platforms() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    platforms = lib.list_platforms()
    assert "shopify" in platforms


def test_shopify_new_content_types_in_list() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    content_types = lib.list_content_types()
    assert "landing_page" in content_types
    assert "email_campaign" in content_types
    assert "social_post" in content_types


def test_shopify_templates_have_constraints() -> None:
    from aeo_shared.content_templates import get_content_template_library

    lib = get_content_template_library()
    for content_type in ["listing", "landing_page", "email_campaign", "social_post"]:
        template = lib.get(content_type, "shopify")
        assert template.constraints, f"{content_type} template should have constraints"
