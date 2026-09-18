"""TikTok Shop API client with mock fallback."""

from __future__ import annotations

import os

from aeo_integrations.tiktok.models import (
    TikTokAdCampaign,
    TikTokAdReport,
    TikTokOrderItem,
    TikTokProduct,
)


class TikTokShopClient:
    def __init__(self, access_token: str | None = None, shop_id: str | None = None) -> None:
        self.access_token = access_token or os.environ.get("TIKTOK_ACCESS_TOKEN")
        self.shop_id = shop_id or os.environ.get("TIKTOK_SHOP_ID")
        self._use_mock = not (self.access_token and self.shop_id)

    def list_orders(
        self,
        *,
        sku: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[TikTokOrderItem]:
        if self._use_mock:
            return self._mock_orders(sku=sku, status=status, limit=limit)
        return self._api_list_orders(sku=sku, status=status, limit=limit)

    def list_products(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[TikTokProduct]:
        if self._use_mock:
            return self._mock_products(status=status, limit=limit)
        return self._api_list_products(status=status, limit=limit)

    def list_ad_campaigns(self, *, limit: int = 20) -> list[TikTokAdCampaign]:
        if self._use_mock:
            return self._mock_ad_campaigns(limit=limit)
        return self._api_list_ad_campaigns(limit=limit)

    def get_ad_report(
        self,
        campaign_id: str,
        *,
        start_date: str,
        end_date: str,
    ) -> list[TikTokAdReport]:
        if self._use_mock:
            return self._mock_ad_report(campaign_id, start_date=start_date, end_date=end_date)
        return self._api_get_ad_report(campaign_id, start_date=start_date, end_date=end_date)

    def _api_list_orders(
        self,
        *,
        sku: str | None,
        status: str | None,
        limit: int,
    ) -> list[TikTokOrderItem]:
        raise NotImplementedError("TikTok API integration pending")

    def _api_list_products(self, *, status: str | None, limit: int) -> list[TikTokProduct]:
        raise NotImplementedError("TikTok API integration pending")

    def _api_list_ad_campaigns(self, *, limit: int) -> list[TikTokAdCampaign]:
        raise NotImplementedError("TikTok API integration pending")

    def _api_get_ad_report(
        self,
        campaign_id: str,
        *,
        start_date: str,
        end_date: str,
    ) -> list[TikTokAdReport]:
        raise NotImplementedError("TikTok API integration pending")

    def _mock_orders(
        self,
        *,
        sku: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[TikTokOrderItem]:
        items = [
            TikTokOrderItem(
                order_id="TT-001",
                sku="TK-SKU-A",
                quantity=2,
                unit_price="29.99",
                product_name="Wireless Earbuds",
                order_status="AwaitingShipment",
                create_time="2026-09-15T10:00:00Z",
                currency="USD",
            ),
            TikTokOrderItem(
                order_id="TT-002",
                sku="TK-SKU-B",
                quantity=1,
                unit_price="49.99",
                product_name="Phone Case",
                order_status="Shipped",
                create_time="2026-09-16T14:30:00Z",
                tracking_number="TT123456789",
                shipping_provider="USPS",
                currency="USD",
            ),
            TikTokOrderItem(
                order_id="TT-003",
                sku="TK-SKU-A",
                quantity=3,
                unit_price="29.99",
                product_name="Wireless Earbuds",
                order_status="Delivered",
                create_time="2026-09-10T09:15:00Z",
                currency="USD",
            ),
        ]
        if sku:
            key = sku.strip().upper()
            items = [i for i in items if i.sku.upper() == key]
        if status:
            items = [i for i in items if i.order_status == status]
        return items[:limit]

    def _mock_products(self, *, status: str | None = None, limit: int = 20) -> list[TikTokProduct]:
        products = [
            TikTokProduct(
                product_id="PROD-001",
                sku="TK-SKU-A",
                title="Wireless Earbuds Pro",
                description="High-quality wireless earbuds with noise cancellation",
                price="29.99",
                stock=150,
                status="ACTIVE",
                brand="AudioTech",
                images=["https://example.com/earbuds1.jpg"],
                create_time="2026-08-01T00:00:00Z",
            ),
            TikTokProduct(
                product_id="PROD-002",
                sku="TK-SKU-B",
                title="Premium Phone Case",
                description="Protective case with military-grade drop protection",
                price="49.99",
                stock=80,
                status="ACTIVE",
                brand="CaseMaster",
                images=["https://example.com/case1.jpg"],
                create_time="2026-08-05T00:00:00Z",
            ),
        ]
        if status:
            products = [p for p in products if p.status == status]
        return products[:limit]

    def _mock_ad_campaigns(self, *, limit: int = 20) -> list[TikTokAdCampaign]:
        campaigns = [
            TikTokAdCampaign(
                campaign_id="AD-001",
                name="Earbuds Promo",
                status="ENABLE",
                budget="100.00",
                ad_type="VIDEO_SHOPPING",
                create_time="2026-09-01T00:00:00Z",
            ),
            TikTokAdCampaign(
                campaign_id="AD-002",
                name="Phone Case Sale",
                status="ENABLE",
                budget="75.00",
                ad_type="LIVE_SHOPPING",
                create_time="2026-09-05T00:00:00Z",
            ),
        ]
        return campaigns[:limit]

    def _mock_ad_report(
        self,
        campaign_id: str,
        *,
        start_date: str,
        end_date: str,
    ) -> list[TikTokAdReport]:
        return [
            TikTokAdReport(
                campaign_id=campaign_id,
                date="2026-09-15",
                impressions=5000,
                clicks=250,
                spend="45.50",
                conversions=15,
                gmv="449.85",
                currency="USD",
            ),
            TikTokAdReport(
                campaign_id=campaign_id,
                date="2026-09-16",
                impressions=4800,
                clicks=230,
                spend="42.30",
                conversions=12,
                gmv="359.88",
                currency="USD",
            ),
        ]
