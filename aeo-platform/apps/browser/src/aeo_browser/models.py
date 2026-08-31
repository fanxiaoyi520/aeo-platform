"""Structured listing data from browser fetch — MS4."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class ListingSnapshot:
    asin: str
    title: str
    bullets: tuple[str, ...]
    price: str
    rating: float | None
    review_count: int | None
    screenshot_path: str
    fetched_at: str
    source: str = "browser"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["bullets"] = list(self.bullets)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ListingSnapshot:
        bullets_raw = data.get("bullets")
        bullets: tuple[str, ...]
        if isinstance(bullets_raw, list):
            bullets = tuple(str(item) for item in bullets_raw if item)
        else:
            bullets = ()
        rating_raw = data.get("rating")
        rating = float(rating_raw) if isinstance(rating_raw, (int, float)) else None
        review_raw = data.get("review_count")
        review_count = int(review_raw) if isinstance(review_raw, int) else None
        return cls(
            asin=str(data.get("asin", "")),
            title=str(data.get("title", "")),
            bullets=bullets,
            price=str(data.get("price", "")),
            rating=rating,
            review_count=review_count,
            screenshot_path=str(data.get("screenshot_path", "")),
            fetched_at=str(data.get("fetched_at", datetime.now(UTC).isoformat())),
            source=str(data.get("source", "browser")),
        )
