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


@dataclass(frozen=True)
class SellerCentralInspection:
    """Read-only Seller Central dashboard snapshot — MV3-05."""

    account_health: dict[str, object]
    listing_status: dict[str, object]
    notifications: list[dict[str, object]]
    screenshots: dict[str, str]
    inspected_at: str
    degraded: bool = False
    degraded_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> SellerCentralInspection:
        screenshots_raw = data.get("screenshots", {})
        screenshots = {str(k): str(v) for k, v in screenshots_raw.items()} if isinstance(screenshots_raw, dict) else {}
        notifications_raw = data.get("notifications", [])
        notifications = [dict(n) for n in notifications_raw if isinstance(n, dict)] if isinstance(notifications_raw, list) else []
        return cls(
            account_health=dict(data.get("account_health", {})) if isinstance(data.get("account_health"), dict) else {},
            listing_status=dict(data.get("listing_status", {})) if isinstance(data.get("listing_status"), dict) else {},
            notifications=notifications,
            screenshots=screenshots,
            inspected_at=str(data.get("inspected_at", datetime.now(UTC).isoformat())),
            degraded=bool(data.get("degraded", False)),
            degraded_reason=str(data.get("degraded_reason", "")),
        )
