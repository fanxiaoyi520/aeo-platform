"""Tests for P3-01: Shopify DTC integration expansion."""

from __future__ import annotations

from decimal import Decimal


class TestShopifyAbandonedCart:
    def test_model_creation(self) -> None:
        from aeo_integrations.shopify.models import ShopifyAbandonedCart

        cart = ShopifyAbandonedCart(
            cart_id="CART-001",
            customer_email="test@example.com",
            total_value=Decimal("75.50"),
            line_count=3,
            abandoned_at="2026-09-01T10:00:00Z",
        )
        assert cart.cart_id == "CART-001"
        assert cart.total_value == Decimal("75.50")
        assert cart.line_count == 3

    def test_model_defaults(self) -> None:
        from aeo_integrations.shopify.models import ShopifyAbandonedCart

        cart = ShopifyAbandonedCart(
            cart_id="CART-002",
            customer_email="user@test.com",
            total_value=Decimal("30.00"),
            line_count=1,
            abandoned_at="2026-09-02T12:00:00Z",
        )
        assert cart.customer_id == ""
        assert cart.recovery_email_sent is False


class TestShopifyCustomer:
    def test_model_creation(self) -> None:
        from aeo_integrations.shopify.models import ShopifyCustomer

        customer = ShopifyCustomer(
            customer_id="CUST-001",
            email="buyer@example.com",
            first_name="Jane",
            last_name="Doe",
            total_spent=Decimal("250.00"),
            orders_count=5,
        )
        assert customer.customer_id == "CUST-001"
        assert customer.total_spent == Decimal("250.00")
        assert customer.orders_count == 5

    def test_model_defaults(self) -> None:
        from aeo_integrations.shopify.models import ShopifyCustomer

        customer = ShopifyCustomer(
            customer_id="CUST-002",
            email="new@example.com",
            first_name="John",
            last_name="Smith",
            total_spent=Decimal("0.00"),
            orders_count=0,
        )
        assert customer.accepts_marketing is False
        assert customer.state == "disabled"


class TestShopifyDiscountCode:
    def test_model_creation(self) -> None:
        from aeo_integrations.shopify.models import ShopifyDiscountCode

        code = ShopifyDiscountCode(
            code_id="DC-001",
            code="SUMMER20",
            discount_type="percentage",
            discount_value=Decimal("20.00"),
            usage_limit=100,
            times_used=45,
        )
        assert code.code == "SUMMER20"
        assert code.discount_value == Decimal("20.00")
        assert code.times_used == 45

    def test_model_defaults(self) -> None:
        from aeo_integrations.shopify.models import ShopifyDiscountCode

        code = ShopifyDiscountCode(
            code_id="DC-002",
            code="FLAT10",
            discount_type="fixed_amount",
            discount_value=Decimal("10.00"),
            usage_limit=0,
            times_used=0,
        )
        assert code.is_active is True


class TestShopifyStoreMetrics:
    def test_model_creation(self) -> None:
        from aeo_integrations.shopify.models import ShopifyStoreMetrics

        metrics = ShopifyStoreMetrics(
            date="2026-09-01",
            sessions=1500,
            orders=45,
            revenue=Decimal("2250.00"),
            conversion_rate=Decimal("0.03"),
        )
        assert metrics.sessions == 1500
        assert metrics.revenue == Decimal("2250.00")

    def test_model_defaults(self) -> None:
        from aeo_integrations.shopify.models import ShopifyStoreMetrics

        metrics = ShopifyStoreMetrics(
            date="2026-09-02",
            sessions=1000,
            orders=30,
            revenue=Decimal("1500.00"),
            conversion_rate=Decimal("0.03"),
        )
        assert metrics.cart_abandonment_rate is None
        assert metrics.avg_order_value is None


class TestStoreClientDTCMethods:
    def test_list_abandoned_carts(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        carts = client.list_abandoned_carts()
        assert len(carts) >= 1
        assert all(hasattr(c, "cart_id") for c in carts)

    def test_list_abandoned_carts_with_limit(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        carts = client.list_abandoned_carts(limit=2)
        assert len(carts) <= 2

    def test_list_customers(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        customers = client.list_customers()
        assert len(customers) >= 1
        assert all(hasattr(c, "customer_id") for c in customers)

    def test_list_customers_with_limit(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        customers = client.list_customers(limit=3)
        assert len(customers) <= 3

    def test_list_discount_codes(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        codes = client.list_discount_codes()
        assert len(codes) >= 1
        assert all(hasattr(c, "code") for c in codes)

    def test_list_discount_codes_filter_active(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        active = client.list_discount_codes(is_active=True)
        assert all(c.is_active for c in active)

    def test_get_store_metrics(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        metrics = client.get_store_metrics()
        assert len(metrics) >= 1
        assert all(hasattr(m, "date") for m in metrics)

    def test_get_store_metrics_with_limit(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        metrics = client.get_store_metrics(limit=3)
        assert len(metrics) <= 3


class TestShopifyApiAdapterDTC:
    def test_list_abandoned_carts_raises(self) -> None:
        import pytest
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        adapter = ShopifyApiAdapter(store_url="test.myshopify.com", access_token="tok")
        with pytest.raises(NotImplementedError):
            adapter.list_abandoned_carts()

    def test_list_customers_raises(self) -> None:
        import pytest
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        adapter = ShopifyApiAdapter(store_url="test.myshopify.com", access_token="tok")
        with pytest.raises(NotImplementedError):
            adapter.list_customers()

    def test_list_discount_codes_raises(self) -> None:
        import pytest
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        adapter = ShopifyApiAdapter(store_url="test.myshopify.com", access_token="tok")
        with pytest.raises(NotImplementedError):
            adapter.list_discount_codes()

    def test_get_store_metrics_raises(self) -> None:
        import pytest
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        adapter = ShopifyApiAdapter(store_url="test.myshopify.com", access_token="tok")
        with pytest.raises(NotImplementedError):
            adapter.get_store_metrics()


class TestDTCMockDataIntegrity:
    def test_abandoned_cart_fields_complete(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        carts = client.list_abandoned_carts()
        for c in carts:
            assert c.cart_id
            assert c.customer_email
            assert c.total_value is not None

    def test_customer_fields_complete(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        customers = client.list_customers()
        for c in customers:
            assert c.customer_id
            assert c.email

    def test_discount_code_fields_complete(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        codes = client.list_discount_codes()
        for c in codes:
            assert c.code_id
            assert c.code

    def test_store_metrics_fields_complete(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        metrics = client.get_store_metrics()
        for m in metrics:
            assert m.date
            assert m.sessions >= 0


class TestTopLevelExport:
    def test_get_store_client_exported(self) -> None:
        from aeo_integrations import get_store_client

        client = get_store_client()
        assert client is not None
        products = client.list_products()
        assert len(products) >= 1
