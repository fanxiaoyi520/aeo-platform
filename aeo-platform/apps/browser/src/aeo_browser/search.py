"""Keyword-based competitor search — MS4 S4-02."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from aeo_browser.config import MAX_COMPETITORS_PER_TASK, amazon_base_url
from aeo_browser.fetcher import fetch_listing


async def search_competitors(
    keyword: str,
    platform: str = "amazon",
    *,
    market: str = "US",
    limit: int = 3,
) -> list[dict[str, object]]:
    """Search public listings by keyword; returns enriched listing snapshots."""
    if platform != "amazon":
        raise ValueError(f"unsupported platform: {platform}")

    limit = max(1, min(limit, MAX_COMPETITORS_PER_TASK))
    from playwright.async_api import async_playwright

    query = quote_plus(keyword.strip())
    url = f"{amazon_base_url(market)}/s?k={query}"

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)

        asins: list[str] = []
        hrefs = await page.locator("div[data-component-type='s-search-result'] h2 a").all()
        for link in hrefs:
            href = await link.get_attribute("href") or ""
            match = re.search(r"/dp/([A-Z0-9]{10})", href.upper())
            if match and match.group(1) not in asins:
                asins.append(match.group(1))
            if len(asins) >= limit:
                break
        await context.close()
        await browser.close()

    results: list[dict[str, object]] = []
    for asin in asins:
        try:
            results.append(await fetch_listing(asin, market=market))
        except Exception:
            results.append({"asin": asin, "source": "search_partial", "title": ""})
    return results
