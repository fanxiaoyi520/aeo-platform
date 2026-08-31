"""Amazon public listing fetch via Playwright — MS4 S4-02."""

from __future__ import annotations

import asyncio
import random
import re
from datetime import UTC, datetime
from typing import Any

from aeo_browser.config import (
    MAX_RETRIES,
    MIN_REQUEST_INTERVAL_SECONDS,
    USER_AGENTS,
    amazon_base_url,
    screenshot_dir,
)
from aeo_browser.models import ListingSnapshot

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


def _parse_rating(text: str) -> float | None:
    match = re.search(r"([\d.]+)\s*out of", text)
    if match:
        return float(match.group(1))
    match = re.search(r"([\d.]+)", text)
    return float(match.group(1)) if match else None


def _parse_review_count(text: str) -> int | None:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


async def _extract_listing(page: Any, asin: str, shot_path: str) -> ListingSnapshot:
    title = (await page.locator("#productTitle").first.text_content() or "").strip()
    if not title:
        title = (await page.locator("h1").first.text_content() or "").strip()

    bullets: list[str] = []
    bullet_nodes = page.locator("#feature-bullets li span.a-list-item")
    count = await bullet_nodes.count()
    for index in range(min(count, 10)):
        text = (await bullet_nodes.nth(index).text_content() or "").strip()
        if text:
            bullets.append(text)

    price = (await page.locator("span.a-price span.a-offscreen").first.text_content() or "").strip()
    if not price:
        price = (await page.locator("#priceblock_ourprice").first.text_content() or "").strip()

    rating_locator = page.locator("#acrPopover span.a-icon-alt").first
    rating_text = (await rating_locator.text_content() or "").strip()
    if not rating_text:
        hook_locator = page.locator("span[data-hook='rating-out-of-text']").first
        rating_text = (await hook_locator.text_content() or "").strip()
    rating = _parse_rating(rating_text)

    review_text = (await page.locator("#acrCustomerReviewText").first.text_content() or "").strip()
    review_count = _parse_review_count(review_text)

    await page.screenshot(path=shot_path, full_page=False)

    return ListingSnapshot(
        asin=asin,
        title=title,
        bullets=tuple(bullets),
        price=price,
        rating=rating,
        review_count=review_count,
        screenshot_path=shot_path,
        fetched_at=datetime.now(UTC).isoformat(),
    )


async def fetch_listing(asin: str, *, market: str = "US") -> dict[str, object]:
    """Fetch a public Amazon listing page by ASIN. Raises on captcha or missing page."""
    from playwright.async_api import async_playwright

    asin = asin.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise ValueError(f"invalid ASIN: {asin}")

    out_dir = screenshot_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    shot_path = str(out_dir / f"{asin}_{stamp}.png")
    url = f"{amazon_base_url(market)}/dp/{asin}"

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        await _throttle()
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    locale="en-US",
                )
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                if response is None or response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status if response else 'no response'}")

                body_text = (await page.locator("body").inner_text()).lower()
                if "captcha" in body_text or "robot check" in body_text:
                    raise RuntimeError("captcha detected")

                snapshot = await _extract_listing(page, asin, shot_path)
                await context.close()
                await browser.close()
                if not snapshot.title:
                    raise RuntimeError("empty title — page layout may have changed")
                return snapshot.to_dict()
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.5 * (attempt + 1))
            continue

    raise RuntimeError(f"fetch_listing failed for {asin}: {last_error}") from last_error
