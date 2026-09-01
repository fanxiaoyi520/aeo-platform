"""Amazon listing adapter tool for orchestrator nodes."""

from __future__ import annotations

from typing import Any

from aeo_integrations.amazon.models import AmazonListing

MARKETPLACE_IDS: dict[str, str] = {
    "US": "ATVPDKIKX0DER",
}


def merge_listing_into_product_info(
    product_info: dict[str, Any],
    listing: AmazonListing,
) -> dict[str, Any]:
    """Merge listing fields into product_info without overwriting user input."""
    merged = dict(product_info)
    scalar_fields = {
        "title": listing.title,
        "brand": listing.brand,
        "asin": listing.asin,
        "listing_status": listing.status,
        "price": str(listing.price) if listing.price is not None else None,
        "currency": listing.currency,
        "fulfillment_channel": listing.fulfillment_channel,
    }
    for key, value in scalar_fields.items():
        if value and not merged.get(key):
            merged[key] = value

    if listing.bullets and not merged.get("bullets"):
        merged["bullets"] = list(listing.bullets)
    if listing.keywords and not merged.get("keywords"):
        merged["keywords"] = list(listing.keywords)

    merged["amazon_listing"] = listing.model_dump(mode="json")
    return merged


def enrich_product_info_from_amazon(
    *,
    sku: str,
    market: str,
    platform: str,
    product_info: dict[str, Any],
) -> tuple[dict[str, Any], AmazonListing | None]:
    """Load Amazon listing via integrations adapter when platform is amazon."""
    if platform != "amazon":
        return product_info, None

    from aeo_integrations.amazon import get_listings_client

    marketplace_id = MARKETPLACE_IDS.get(market.upper(), MARKETPLACE_IDS["US"])
    try:
        listing = get_listings_client().get_listing(sku, marketplace_id=marketplace_id)
    except KeyError:
        return product_info, None

    return merge_listing_into_product_info(product_info, listing), listing
