"""Seller Central read-only inspection via Playwright — MV3-05."""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime
from typing import Any

from aeo_browser.config import (
    MAX_RETRIES,
    MIN_REQUEST_INTERVAL_SECONDS,
    SELLER_CENTRAL_BASE_URL,
    SELLER_CENTRAL_PAGES,
    USER_AGENTS,
    is_headless,
    seller_central_screenshot_dir,
    seller_central_storage_state,
)
from aeo_browser.models import SellerCentralInspection

_last_request_at: float = 0.0
_request_lock = asyncio.Lock()


async def _throttle() -> None:
    global _last_request_at
    async with _request_lock:
        now = asyncio.get_event_loop().time()
        wait = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request_at)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request_at = asyncio.get_event_loop().time()


async def _extract_account_health(page: Any) -> dict[str, object]:
    body_text = await page.locator("body").inner_text()
    health: dict[str, object] = {"raw_text_length": len(body_text)}

    for line in body_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if "account health" in lower or "voice of the customer" in lower:
            health["page_title"] = line
            break

    violation_markers = ["policy violation", "ip complaint", "account health rating"]
    found_violations: list[str] = []
    for marker in violation_markers:
        if marker in body_text.lower():
            found_violations.append(marker)
    health["detected_indicators"] = found_violations

    return health


async def _extract_listing_status(page: Any) -> dict[str, object]:
    body_text = await page.locator("body").inner_text()
    status: dict[str, object] = {"raw_text_length": len(body_text)}

    status_keywords = ["active", "inactive", "suppressed", "closed"]
    found_statuses: list[str] = []
    for kw in status_keywords:
        if kw in body_text.lower():
            found_statuses.append(kw)
    status["detected_statuses"] = found_statuses

    return status


async def _extract_notifications(page: Any) -> list[dict[str, object]]:
    body_text = await page.locator("body").inner_text()
    notifications: list[dict[str, object]] = []

    for line in body_text.split("\n"):
        line = line.strip()
        if len(line) > 10 and len(line) < 300:
            lower = line.lower()
            if any(kw in lower for kw in ["alert", "warning", "action required", "notification", "performance"]):
                notifications.append({"text": line, "type": "notification"})
                if len(notifications) >= 10:
                    break

    return notifications


async def _scrape_page(
    page: Any,
    page_name: str,
    page_path: str,
    stamp: str,
) -> dict[str, object]:
    url = f"{SELLER_CENTRAL_BASE_URL}{page_path}"
    await _throttle()
    response = await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
    if response is None or response.status >= 400:
        raise RuntimeError(f"HTTP {response.status if response else 'no response'} for {page_name}")

    body_text = (await page.locator("body").inner_text()).lower()
    if "captcha" in body_text or "robot check" in body_text:
        raise RuntimeError(f"captcha detected on {page_name}")

    out_dir = seller_central_screenshot_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    shot_path = str(out_dir / f"{page_name}_{stamp}.png")
    await page.screenshot(path=shot_path, full_page=False)

    if page_name == "account_health":
        return {"data": await _extract_account_health(page), "screenshot": shot_path}
    elif page_name == "listing_status":
        return {"data": await _extract_listing_status(page), "screenshot": shot_path}
    else:
        return {"data": await _extract_notifications(page), "screenshot": shot_path}


async def inspect_seller_central() -> dict[str, object]:
    """Read-only Seller Central inspection. Returns SellerCentralInspection as dict.

    Raises on auth failure or captcha. Caller should handle degradation.
    """
    from playwright.async_api import async_playwright

    storage = seller_central_storage_state()
    if not storage:
        raise RuntimeError("SELLER_CENTRAL_STORAGE_STATE not set or file missing")

    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    results: dict[str, dict[str, object]] = {}
    screenshots: dict[str, str] = {}

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=is_headless())
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    locale="en-US",
                    storage_state=storage,
                )
                page = await context.new_page()

                for page_name, page_path in SELLER_CENTRAL_PAGES.items():
                    scraped = await _scrape_page(page, page_name, page_path, stamp)
                    results[page_name] = scraped["data"]  # type: ignore[assignment]
                    screenshots[page_name] = scraped["screenshot"]  # type: ignore[assignment]

                await context.close()
                await browser.close()

            inspection = SellerCentralInspection(
                account_health=results.get("account_health", {}),  # type: ignore[arg-type]
                listing_status=results.get("listing_status", {}),  # type: ignore[arg-type]
                notifications=results.get("notifications", []),  # type: ignore[arg-type]
                screenshots=screenshots,
                inspected_at=datetime.now(UTC).isoformat(),
            )
            return inspection.to_dict()

        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.5 * (attempt + 1))
            continue

    raise RuntimeError(f"inspect_seller_central failed: {last_error}") from last_error


def build_degraded_inspection(reason: str) -> dict[str, object]:
    """Return a degraded inspection result when browser inspection is unavailable."""
    inspection = SellerCentralInspection(
        account_health={},
        listing_status={},
        notifications=[],
        screenshots={},
        inspected_at=datetime.now(UTC).isoformat(),
        degraded=True,
        degraded_reason=reason,
    )
    return inspection.to_dict()
