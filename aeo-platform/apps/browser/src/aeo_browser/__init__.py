"""Playwright browser automation — MS4."""

from aeo_browser.config import is_browser_enabled
from aeo_browser.fetcher import fetch_listing
from aeo_browser.search import search_competitors

__all__ = ["fetch_listing", "is_browser_enabled", "search_competitors"]
