"""Optional listing persistence hook — wired by API on startup."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

ListingSaver = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]

_saver: ListingSaver | None = None


def set_listing_saver(saver: ListingSaver | None) -> None:
    global _saver
    _saver = saver


async def save_listing_version(task_id: str, content: dict[str, Any]) -> dict[str, Any]:
    if _saver is None:
        return {"version": 1, "persisted": False}
    return await _saver(task_id, content)
