"""Playwright browser automation — MS4 + MV3-05."""

from aeo_browser.config import is_browser_enabled
from aeo_browser.fetcher import fetch_listing
from aeo_browser.search import search_competitors
from aeo_browser.seller_central import build_degraded_inspection, inspect_seller_central

__all__ = [
    "build_degraded_inspection",
    "fetch_listing",
    "inspect_seller_central",
    "is_browser_enabled",
    "search_competitors",
]
