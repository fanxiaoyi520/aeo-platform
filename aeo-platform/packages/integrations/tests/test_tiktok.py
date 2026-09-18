"""P7-08: Tests for TikTok Shop integration."""

from __future__ import annotations

from aeo_integrations.tiktok import TikTokShopClient


class TestTikTokShopClient:
    def test_client_initialization_mock_mode(self) -> None:
        client = TikTokShopClient()
        assert client._use_mock is True

    def test_client_initialization_with_credentials(self) -> None:
        client = TikTokShopClient(access_token="test_token", shop_id="test_shop")
        assert client._use_mock is False

    def test_list_orders_mock(self) -> None:
        client = TikTokShopClient()
        orders = client.list_orders()

        assert len(orders) == 3
        assert orders[0].order_id == "TT-001"
        assert orders[0].sku == "TK-SKU-A"
        assert orders[0].quantity == 2
        assert orders[0].order_status == "AwaitingShipment"

    def test_list_orders_with_sku_filter(self) -> None:
        client = TikTokShopClient()
        orders = client.list_orders(sku="TK-SKU-A")

        assert len(orders) == 2
        assert all(o.sku == "TK-SKU-A" for o in orders)

    def test_list_orders_with_status_filter(self) -> None:
        client = TikTokShopClient()
        orders = client.list_orders(status="Shipped")

        assert len(orders) == 1
        assert orders[0].order_status == "Shipped"

    def test_list_orders_with_limit(self) -> None:
        client = TikTokShopClient()
        orders = client.list_orders(limit=2)

        assert len(orders) == 2

    def test_list_products_mock(self) -> None:
        client = TikTokShopClient()
        products = client.list_products()

        assert len(products) == 2
        assert products[0].product_id == "PROD-001"
        assert products[0].sku == "TK-SKU-A"
        assert products[0].title == "Wireless Earbuds Pro"
        assert products[0].price == "29.99"
        assert products[0].stock == 150

    def test_list_products_with_status_filter(self) -> None:
        client = TikTokShopClient()
        products = client.list_products(status="ACTIVE")

        assert len(products) == 2
        assert all(p.status == "ACTIVE" for p in products)

    def test_list_ad_campaigns_mock(self) -> None:
        client = TikTokShopClient()
        campaigns = client.list_ad_campaigns()

        assert len(campaigns) == 2
        assert campaigns[0].campaign_id == "AD-001"
        assert campaigns[0].name == "Earbuds Promo"
        assert campaigns[0].status == "ENABLE"
        assert campaigns[0].budget == "100.00"

    def test_get_ad_report_mock(self) -> None:
        client = TikTokShopClient()
        report = client.get_ad_report("AD-001", start_date="2026-09-15", end_date="2026-09-16")

        assert len(report) == 2
        assert report[0].campaign_id == "AD-001"
        assert report[0].date == "2026-09-15"
        assert report[0].impressions == 5000
        assert report[0].clicks == 250
        assert report[0].spend == "45.50"
        assert report[0].conversions == 15

    def test_api_methods_raise_not_implemented(self) -> None:
        import pytest

        client = TikTokShopClient(access_token="token", shop_id="shop")

        with pytest.raises(NotImplementedError):
            client._api_list_orders(sku=None, status=None, limit=20)

        with pytest.raises(NotImplementedError):
            client._api_list_products(status=None, limit=20)
