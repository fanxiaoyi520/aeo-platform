from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import requests

from aeo_integrations.amazon.config import AmazonSettings
from aeo_integrations.amazon.models import (
    AmazonAdCampaign,
    AmazonAdSpendSnapshot,
    AmazonInventoryItem,
    AmazonListing,
    AmazonOrderItem,
)

logger = logging.getLogger(__name__)


def _build_client_kwargs(settings: AmazonSettings) -> dict[str, Any]:
    from sp_api.base import Marketplaces  # type: ignore[import-untyped]

    marketplace = Marketplaces.US
    for member in Marketplaces:
        if member.marketplace_id == settings.marketplace_id:
            marketplace = member
            break

    credentials = {
        "lwa_app_id": settings.sp_api_client_id,
        "lwa_client_secret": settings.sp_api_client_secret,
    }

    return {
        "marketplace": marketplace,
        "refresh_token": settings.sp_api_refresh_token,
        "credentials": credentials,
    }


def _safe_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, dict):
        amount = value.get("Amount") or value.get("amount")
        if amount is not None:
            return Decimal(str(amount))
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


class SpApiListingsAdapter:
    def __init__(self, settings: AmazonSettings) -> None:
        self._settings = settings

    @property
    def data_source(self) -> str:
        return "spapi"

    def _get_client(self) -> Any:
        from sp_api.api import CatalogItems  # type: ignore[import-untyped]

        kwargs = _build_client_kwargs(self._settings)
        return CatalogItems(version="2022-04-01", **kwargs)

    def get_listing(self, sku: str, *, marketplace_id: str | None = None) -> AmazonListing:
        client = self._get_client()
        mp_id = marketplace_id or self._settings.marketplace_id
        response = client.search_catalog_items(
            identifiers=sku,
            identifiersType="SKU",
            marketplaceIds=[mp_id],
            includedData=["summaries", "identifiers"],
        )
        items = response.payload.get("items", [])
        if not items:
            msg = f"Listing not found for SKU: {sku}"
            raise KeyError(msg)
        return self._map_item(items[0], sku)

    def list_listings(
        self,
        *,
        marketplace_id: str | None = None,
        limit: int = 20,
    ) -> list[AmazonListing]:
        client = self._get_client()
        mp_id = marketplace_id or self._settings.marketplace_id
        response = client.search_catalog_items(
            marketplaceIds=[mp_id],
            includedData=["summaries", "identifiers"],
            pageSize=limit,
        )
        items = response.payload.get("items", [])
        return [self._map_item(item, "") for item in items[:limit]]

    def _map_item(self, item: dict[str, Any], fallback_sku: str) -> AmazonListing:
        summaries = item.get("summaries", [{}])
        summary = summaries[0] if summaries else {}
        identifiers = item.get("identifiers", [{}])
        identifier = identifiers[0] if identifiers else {}

        sku_value = (
            (
                identifier.get("identifier", {}).get("skuIdentifier")
                if isinstance(identifier.get("identifier"), dict)
                else None
            )
            or fallback_sku
            or summary.get("asin", "")
        )

        return AmazonListing(
            sku=sku_value,
            seller_sku=sku_value,
            asin=item.get("asin") or summary.get("asin"),
            marketplace_id=self._settings.marketplace_id,
            status="ACTIVE" if summary.get("itemClassification") != "SUPPRESSED" else "SUPPRESSED",
            title=summary.get("itemName", "") or summary.get("title", ""),
            brand=summary.get("brand", ""),
            price=_safe_decimal(summary.get("listPrice") or summary.get("price")),
            currency=summary.get("currencyCode", "USD") or "USD",
        )


class SpApiOrdersAdapter:
    def __init__(self, settings: AmazonSettings) -> None:
        self._settings = settings

    @property
    def data_source(self) -> str:
        return "spapi"

    def _get_client(self) -> Any:
        from sp_api.api import Orders

        kwargs = _build_client_kwargs(self._settings)
        return Orders(**kwargs)

    def list_orders(
        self,
        *,
        sku: str | None = None,
        limit: int = 20,
    ) -> list[AmazonOrderItem]:
        client = self._get_client()
        created_after = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        response = client.get_orders(
            MarketplaceIds=[self._settings.marketplace_id],
            CreatedAfter=created_after,
            MaxResultsPerPage=min(limit, 100),
        )
        orders = response.payload.get("Orders", [])
        result: list[AmazonOrderItem] = []

        for order in orders[:limit]:
            order_id = order.get("AmazonOrderId", "")
            try:
                items_response = client.get_order_items(order_id)
                order_items = items_response.payload.get("OrderItems", [])
            except Exception:
                logger.warning("Failed to fetch items for order %s", order_id)
                order_items = []

            for item in order_items:
                item_sku = item.get("SellerSKU", "")
                if sku and item_sku.upper() != sku.strip().upper():
                    continue
                result.append(self._map_order_item(order, item))

        return result[:limit]

    def _map_order_item(self, order: dict[str, Any], item: dict[str, Any]) -> AmazonOrderItem:
        price_info = item.get("ItemPrice", {})
        return AmazonOrderItem(
            order_id=order.get("AmazonOrderId", ""),
            sku=item.get("SellerSKU", ""),
            quantity=item.get("QuantityOrdered", 0),
            item_price=_safe_decimal(price_info.get("Amount") if price_info else None),
            currency=price_info.get("CurrencyCode", "USD") if price_info else "USD",
            order_status=order.get("OrderStatus", "Unshipped"),
            purchase_date=order.get("PurchaseDate", ""),
        )


class SpApiAdvertisingAdapter:
    def __init__(self, settings: AmazonSettings) -> None:
        self._settings = settings

    @property
    def data_source(self) -> str:
        return "spapi"

    def _get_base_url(self) -> str:
        region_map = {
            "na": "https://advertising-api.amazon.com",
            "eu": "https://advertising-api-eu.amazon.com",
            "fe": "https://advertising-api-fe.amazon.com",
        }
        return region_map.get(self._settings.ad_api_region, region_map["na"])

    def _get_headers(self) -> dict[str, str]:
        from aeo_integrations.amazon.auth import get_access_token

        token = get_access_token()
        return {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "Amazon-Ad-API-Client-Id": self._settings.sp_api_client_id,
        }

    def get_campaign(self, campaign_id: str) -> AmazonAdCampaign:
        url = f"{self._get_base_url()}/v2/sp/campaigns/{campaign_id}"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return self._map_campaign(response.json())

    def list_campaigns(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[AmazonAdCampaign]:
        url = f"{self._get_base_url()}/v2/sp/campaigns"
        params: dict[str, Any] = {"pageSize": limit}
        if status:
            params["stateFilter"] = status
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return [self._map_campaign(c) for c in response.json()[:limit]]

    def list_spend_snapshots(
        self,
        *,
        campaign_id: str | None = None,
        limit: int = 50,
    ) -> list[AmazonAdSpendSnapshot]:
        url = f"{self._get_base_url()}/v2/sp/campaigns/report"
        body: dict[str, Any] = {
            "reportDate": datetime.now(UTC).strftime("%Y%m%d"),
            "metrics": ["cost", "impressions", "clicks", "attributedSales"],
        }
        if campaign_id:
            body["campaignIdFilter"] = {"campaignIds": [campaign_id]}

        response = requests.post(url, headers=self._get_headers(), json=body, timeout=30)
        response.raise_for_status()
        return [self._map_snapshot(s) for s in response.json()[:limit]]

    def _map_campaign(self, data: dict[str, Any]) -> AmazonAdCampaign:
        from typing import Literal

        status_map: dict[str, Literal["enabled", "paused", "archived"]] = {
            "enabled": "enabled",
            "paused": "paused",
            "archived": "archived",
        }
        raw_state = data.get("state", "enabled")
        return AmazonAdCampaign(
            campaign_id=str(data.get("campaignId", "")),
            name=data.get("name", ""),
            status=status_map.get(raw_state, "enabled"),
            campaign_type="sponsored_products",
            daily_budget=_safe_decimal(data.get("dailyBudget")),
            currency=data.get("currencyCode", "USD") or "USD",
            start_date=data.get("startDate", ""),
            end_date=data.get("endDate"),
        )

    def _map_snapshot(self, data: dict[str, Any]) -> AmazonAdSpendSnapshot:
        return AmazonAdSpendSnapshot(
            campaign_id=str(data.get("campaignId", "")),
            snapshot_date=data.get("date", ""),
            spend=_safe_decimal(data.get("cost")),
            impressions=data.get("impressions", 0),
            clicks=data.get("clicks", 0),
            attributed_gmv=_safe_decimal(data.get("attributedSales")),
            currency="USD",
        )


class SpApiInventoryAdapter:
    def __init__(self, settings: AmazonSettings) -> None:
        self._settings = settings

    @property
    def data_source(self) -> str:
        return "spapi"

    def _get_client(self) -> Any:
        from sp_api.api import Inventories

        kwargs = _build_client_kwargs(self._settings)
        return Inventories(**kwargs)

    def get_inventory(self, sku: str) -> AmazonInventoryItem:
        client = self._get_client()
        response = client.get_inventory_summary_marketplace(
            sellerSkus=sku,
        )
        summaries = response.payload.get("inventorySummaries", [])
        if not summaries:
            msg = f"Inventory not found for SKU: {sku}"
            raise KeyError(msg)
        return self._map_summary(summaries[0], sku)

    def list_inventory(
        self,
        *,
        fulfillment_channel: str | None = None,
        limit: int = 50,
    ) -> list[AmazonInventoryItem]:
        client = self._get_client()
        response = client.get_inventory_summary_marketplace()
        summaries = response.payload.get("inventorySummaries", [])
        items = [self._map_summary(s, s.get("sellerSku", "")) for s in summaries[:limit]]
        if fulfillment_channel:
            items = [i for i in items if i.fulfillment_channel == fulfillment_channel]
        return items

    def _map_summary(self, summary: dict[str, Any], fallback_sku: str) -> AmazonInventoryItem:
        quantities = summary.get("inventoryDetails", {}).get("totalQuantity", {})
        return AmazonInventoryItem(
            sku=summary.get("sellerSku", "") or fallback_sku,
            fulfillment_channel="AFN",
            available_quantity=quantities.get("availableQuantity", 0) or 0,
            inbound_quantity=quantities.get("inboundWorkingQuantity", 0) or 0,
            reserved_quantity=quantities.get("reservedQuantity", 0) or 0,
            warehouse=summary.get("fnSku", ""),
            last_updated=summary.get("lastUpdatedTime", ""),
        )
