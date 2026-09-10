"""MV3-05 — Seller Central read-only inspection tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aeo_browser.models import SellerCentralInspection
from aeo_browser.seller_central import build_degraded_inspection


def test_seller_central_inspection_roundtrip() -> None:
    inspection = SellerCentralInspection(
        account_health={"detected_indicators": ["policy violation"]},
        listing_status={"detected_statuses": ["active", "suppressed"]},
        notifications=[{"text": "Action required: update listing", "type": "notification"}],
        screenshots={"account_health": "/tmp/ah.png", "listing_status": "/tmp/ls.png"},
        inspected_at="2026-09-10T12:00:00",
    )
    data = inspection.to_dict()
    restored = SellerCentralInspection.from_dict(data)
    assert restored.account_health == inspection.account_health
    assert restored.listing_status == inspection.listing_status
    assert len(restored.notifications) == 1
    assert restored.screenshots == inspection.screenshots
    assert restored.degraded is False


def test_seller_central_inspection_from_dict_defaults() -> None:
    restored = SellerCentralInspection.from_dict(
        {
            "inspected_at": "2026-09-10T12:00:00",
        }
    )
    assert restored.account_health == {}
    assert restored.listing_status == {}
    assert restored.notifications == []
    assert restored.screenshots == {}
    assert restored.degraded is False


def test_build_degraded_inspection() -> None:
    result = build_degraded_inspection("browser disabled")
    assert result["degraded"] is True
    assert result["degraded_reason"] == "browser disabled"
    assert result["account_health"] == {}
    assert result["listing_status"] == {}
    assert result["notifications"] == []
    assert result["screenshots"] == {}
    assert "inspected_at" in result


@pytest.mark.asyncio
async def test_inspect_seller_central_raises_without_storage_state() -> None:
    from aeo_browser.seller_central import inspect_seller_central

    storage_patch = patch(
        "aeo_browser.seller_central.seller_central_storage_state",
        return_value=None,
    )
    with storage_patch, pytest.raises(RuntimeError, match="SELLER_CENTRAL_STORAGE_STATE"):
        await inspect_seller_central()


@pytest.mark.asyncio
async def test_inspect_seller_central_captcha_raises() -> None:
    from aeo_browser.seller_central import inspect_seller_central

    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(return_value=MagicMock(status=200))
    mock_page.locator = MagicMock()
    mock_page.locator.return_value.inner_text = AsyncMock(
        return_value="captcha detected — robot check"
    )
    mock_page.screenshot = AsyncMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_context.close = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_pw_instance = AsyncMock()
    mock_pw_instance.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_pw_instance.__aexit__ = AsyncMock(return_value=False)

    storage_patch = patch(
        "aeo_browser.seller_central.seller_central_storage_state",
        return_value="/tmp/fake_state.json",
    )
    pw_patch = patch("playwright.async_api.async_playwright", return_value=mock_pw_instance)
    with storage_patch, pw_patch, pytest.raises(RuntimeError, match="captcha"):
        await inspect_seller_central()


@pytest.mark.asyncio
async def test_inspect_seller_central_success() -> None:
    from aeo_browser.seller_central import inspect_seller_central

    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(return_value=MagicMock(status=200))
    mock_page.screenshot = AsyncMock()

    page_texts = [
        "Account Health Rating: Good. Voice of the Customer: satisfactory.",
        "Your listings are active and ready. 3 inactive listings need attention.",
        (
            "Action Required: Update your shipping settings. "
            "Performance Notification: late shipment rate increased."
        ),
    ]
    call_idx = 0

    async def mock_inner_text() -> str:
        nonlocal call_idx
        text = page_texts[call_idx] if call_idx < len(page_texts) else "empty"
        call_idx += 1
        return text

    mock_locator_obj = MagicMock()
    mock_locator_obj.inner_text = mock_inner_text

    def locator_side_effect(selector: str) -> MagicMock:
        return mock_locator_obj

    mock_page.locator = MagicMock(side_effect=locator_side_effect)

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_context.close = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_pw_instance = AsyncMock()
    mock_pw_instance.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_pw_instance.__aexit__ = AsyncMock(return_value=False)

    storage_patch = patch(
        "aeo_browser.seller_central.seller_central_storage_state",
        return_value="/tmp/fake_state.json",
    )
    pw_patch = patch("playwright.async_api.async_playwright", return_value=mock_pw_instance)
    throttle_patch = patch("aeo_browser.seller_central._throttle", new_callable=AsyncMock)
    with storage_patch, pw_patch, throttle_patch:
        result = await inspect_seller_central()

    assert result["degraded"] is False
    assert "account_health" in result
    assert "listing_status" in result
    assert "notifications" in result
    assert "screenshots" in result
    screenshots = result["screenshots"]
    assert isinstance(screenshots, dict)
    assert len(screenshots) == 3
    assert "inspected_at" in result


def test_config_seller_central_pages() -> None:
    from aeo_browser.config import SELLER_CENTRAL_BASE_URL, SELLER_CENTRAL_PAGES

    assert SELLER_CENTRAL_BASE_URL == "https://sellercentral.amazon.com"
    assert "account_health" in SELLER_CENTRAL_PAGES
    assert "listing_status" in SELLER_CENTRAL_PAGES
    assert "notifications" in SELLER_CENTRAL_PAGES


def test_seller_central_screenshot_dir() -> None:
    from aeo_browser.config import seller_central_screenshot_dir

    path = seller_central_screenshot_dir()
    assert str(path).endswith("seller-central")
