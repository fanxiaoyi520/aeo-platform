"""Browser automation configuration — MS4."""

from __future__ import annotations

import os
from pathlib import Path

MAX_COMPETITORS_PER_TASK = 5
MIN_REQUEST_INTERVAL_SECONDS = 3.0
MAX_RETRIES = 2
MAX_CONCURRENT_CONTEXTS = 2

USER_AGENTS: tuple[str, ...] = (
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
)


def is_browser_enabled() -> bool:
    return os.getenv("BROWSER_ENABLED", "false").lower() in ("1", "true", "yes")


def is_headless() -> bool:
    return os.getenv("BROWSER_HEADLESS", "true").lower() not in ("0", "false", "no")


def screenshot_dir() -> Path:
    raw = os.getenv("BROWSER_SCREENSHOT_DIR", "data/screenshots")
    return Path(raw)


def amazon_base_url(market: str = "US") -> str:
    hosts = {"US": "https://www.amazon.com", "UK": "https://www.amazon.co.uk"}
    return hosts.get(market.upper(), "https://www.amazon.com")
