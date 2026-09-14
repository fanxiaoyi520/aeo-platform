"""P6-04: Billing service layer tests."""

import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

import pytest

from aeo_api.billing.config import BillingSettings
from aeo_api.billing.service import (
    BillingServiceError,
    _extract_plan_from_price_id,
    _ts_from_stripe,
    create_checkout_session,
    create_portal_session,
    handle_plan_change,
    sync_invoice,
    sync_subscription,
)


def test_ts_from_stripe_none() -> None:
    assert _ts_from_stripe(None) is None


def test_ts_from_stripe_valid() -> None:
    result = _ts_from_stripe(1700000000)
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc


def test_extract_plan_from_price_id_pro() -> None:
    settings = BillingSettings(price_pro_monthly="price_pro_123")
    with patch("aeo_api.billing.service.get_billing_settings", return_value=settings):
        assert _extract_plan_from_price_id("price_pro_123") == "pro"


def test_extract_plan_from_price_id_enterprise() -> None:
    settings = BillingSettings(price_enterprise_monthly="price_ent_456")
    with patch("aeo_api.billing.service.get_billing_settings", return_value=settings):
        assert _extract_plan_from_price_id("price_ent_456") == "enterprise"


def test_extract_plan_from_price_id_unknown() -> None:
    settings = BillingSettings()
    with patch("aeo_api.billing.service.get_billing_settings", return_value=settings):
        assert _extract_plan_from_price_id("price_unknown") == "free"


@pytest.mark.asyncio
async def test_create_checkout_session_billing_disabled() -> None:
    session = AsyncMock()
    settings = BillingSettings(api_key="")
    with pytest.raises(BillingServiceError, match="Billing not configured"):
        await create_checkout_session(session, uuid.uuid4(), price_id="price_test", settings=settings)


@pytest.mark.asyncio
async def test_create_checkout_session_tenant_not_found() -> None:
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    settings = BillingSettings(api_key="sk_test_123")
    with pytest.raises(BillingServiceError, match="Tenant not found"):
        await create_checkout_session(session, uuid.uuid4(), price_id="price_test", settings=settings)


@pytest.mark.asyncio
async def test_create_checkout_session_success() -> None:
    tenant_id = uuid.uuid4()
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.stripe_customer_id = "cus_test123"

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = tenant
    session.execute.return_value = result_mock

    mock_checkout = MagicMock()
    mock_checkout.url = "https://checkout.stripe.com/test"
    mock_checkout.id = "cs_test_session"

    settings = BillingSettings(api_key="sk_test_123")

    with patch("aeo_api.billing.service.stripe.checkout.Session.create", return_value=mock_checkout):
        result = await create_checkout_session(
            session, tenant_id, price_id="price_pro", settings=settings
        )

    assert result["checkout_url"] == "https://checkout.stripe.com/test"
    assert result["session_id"] == "cs_test_session"


@pytest.mark.asyncio
async def test_create_checkout_session_no_customer() -> None:
    tenant_id = uuid.uuid4()
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.stripe_customer_id = None

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = tenant
    session.execute.return_value = result_mock

    mock_checkout = MagicMock()
    mock_checkout.url = "https://checkout.stripe.com/test"
    mock_checkout.id = "cs_test_session"

    settings = BillingSettings(api_key="sk_test_123")

    with patch("aeo_api.billing.service.stripe.checkout.Session.create", return_value=mock_checkout) as mock_create:
        await create_checkout_session(session, tenant_id, price_id="price_pro", settings=settings)

    call_kwargs = mock_create.call_args[1]
    assert "customer" not in call_kwargs
    assert call_kwargs["customer_creation"] == "always"


@pytest.mark.asyncio
async def test_create_portal_session_billing_disabled() -> None:
    session = AsyncMock()
    settings = BillingSettings(api_key="")
    with pytest.raises(BillingServiceError, match="Billing not configured"):
        await create_portal_session(session, uuid.uuid4(), settings=settings)


@pytest.mark.asyncio
async def test_create_portal_session_no_customer() -> None:
    tenant = MagicMock()
    tenant.stripe_customer_id = None

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = tenant
    session.execute.return_value = result_mock

    settings = BillingSettings(api_key="sk_test_123")
    with pytest.raises(BillingServiceError, match="no Stripe customer"):
        await create_portal_session(session, uuid.uuid4(), settings=settings)


@pytest.mark.asyncio
async def test_create_portal_session_success() -> None:
    tenant = MagicMock()
    tenant.stripe_customer_id = "cus_test123"

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = tenant
    session.execute.return_value = result_mock

    mock_portal = MagicMock()
    mock_portal.url = "https://billing.stripe.com/test"
    mock_portal.id = "bps_test"

    settings = BillingSettings(api_key="sk_test_123")

    with patch(
        "aeo_api.billing.service.stripe.billing_portal.Session.create",
        return_value=mock_portal,
    ):
        result = await create_portal_session(session, uuid.uuid4(), settings=settings)

    assert result["portal_url"] == "https://billing.stripe.com/test"


@pytest.mark.asyncio
async def test_sync_subscription_new() -> None:
    tenant_id = uuid.uuid4()
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.stripe_customer_id = "cus_test"

    session = AsyncMock()

    empty_result = MagicMock()
    empty_result.scalar_one_or_none.return_value = None

    tenant_result = MagicMock()
    tenant_result.scalar_one_or_none.return_value = tenant

    session.execute.side_effect = [empty_result, tenant_result]

    sub_data = {
        "id": "sub_test123",
        "customer": "cus_test",
        "status": "active",
        "current_period_start": 1700000000,
        "current_period_end": 1700086400,
        "items": {"data": [{"price": {"id": "price_pro"}}]},
    }

    settings = BillingSettings(price_pro_monthly="price_pro")
    with patch("aeo_api.billing.service.get_billing_settings", return_value=settings):
        result = await sync_subscription(session, sub_data)

    assert result.stripe_subscription_id == "sub_test123"
    assert result.stripe_customer_id == "cus_test"
    assert result.status == "active"
    assert result.plan == "pro"
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_sync_subscription_existing() -> None:
    existing_sub = MagicMock()
    existing_sub.stripe_subscription_id = "sub_existing"

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing_sub
    session.execute.return_value = result_mock

    sub_data = {
        "id": "sub_existing",
        "customer": "cus_test",
        "status": "past_due",
        "current_period_start": 1700000000,
        "current_period_end": 1700086400,
        "cancel_at_period_end": True,
        "items": {"data": []},
    }

    settings = BillingSettings()
    with patch("aeo_api.billing.service.get_billing_settings", return_value=settings):
        result = await sync_subscription(session, sub_data)

    assert result is existing_sub
    assert result.status == "past_due"
    assert result.cancel_at_period_end is True
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_sync_subscription_missing_id() -> None:
    session = AsyncMock()
    with pytest.raises(BillingServiceError, match="Missing subscription id"):
        await sync_subscription(session, {})


@pytest.mark.asyncio
async def test_sync_subscription_with_stripe_object() -> None:
    stripe_obj = MagicMock()
    stripe_obj.to_dict.return_value = {
        "id": "sub_obj_test",
        "customer": "cus_test",
        "status": "active",
        "items": {"data": []},
    }

    tenant = MagicMock()
    tenant.id = uuid.uuid4()
    tenant.stripe_customer_id = "cus_test"

    session = AsyncMock()
    empty_result = MagicMock()
    empty_result.scalar_one_or_none.return_value = None
    tenant_result = MagicMock()
    tenant_result.scalar_one_or_none.return_value = tenant
    session.execute.side_effect = [empty_result, tenant_result]

    settings = BillingSettings()
    with patch("aeo_api.billing.service.get_billing_settings", return_value=settings):
        result = await sync_subscription(session, stripe_obj)

    assert result.stripe_subscription_id == "sub_obj_test"


@pytest.mark.asyncio
async def test_handle_plan_change_success() -> None:
    tenant_id = uuid.uuid4()
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.plan = "free"

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = tenant
    session.execute.return_value = result_mock

    result = await handle_plan_change(session, tenant_id, "pro")

    assert result.plan == "pro"
    assert result is tenant


@pytest.mark.asyncio
async def test_handle_plan_change_tenant_not_found() -> None:
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    with pytest.raises(BillingServiceError, match="Tenant not found"):
        await handle_plan_change(session, uuid.uuid4(), "pro")


@pytest.mark.asyncio
async def test_sync_invoice_new() -> None:
    tenant_id = uuid.uuid4()
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.stripe_customer_id = "cus_test"

    session = AsyncMock()
    empty_result = MagicMock()
    empty_result.scalar_one_or_none.return_value = None
    tenant_result = MagicMock()
    tenant_result.scalar_one_or_none.return_value = tenant
    session.execute.side_effect = [empty_result, tenant_result]

    inv_data = {
        "id": "in_test123",
        "customer": "cus_test",
        "subscription": "sub_test",
        "status": "paid",
        "amount_due": 2000,
        "currency": "usd",
        "invoice_pdf": "https://stripe.com/pdf",
        "hosted_invoice_url": "https://stripe.com/invoice",
    }

    result = await sync_invoice(session, inv_data)

    assert result.stripe_invoice_id == "in_test123"
    assert result.status == "paid"
    assert result.amount_due == 2000
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_sync_invoice_existing() -> None:
    existing_inv = MagicMock()
    existing_inv.stripe_invoice_id = "in_existing"

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing_inv
    session.execute.return_value = result_mock

    inv_data = {
        "id": "in_existing",
        "customer": "cus_test",
        "status": "void",
        "amount_due": 0,
        "currency": "usd",
    }

    result = await sync_invoice(session, inv_data)

    assert result is existing_inv
    assert result.status == "void"
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_sync_invoice_missing_id() -> None:
    session = AsyncMock()
    with pytest.raises(BillingServiceError, match="Missing invoice id"):
        await sync_invoice(session, {})


@pytest.mark.asyncio
async def test_sync_invoice_with_paid_at() -> None:
    tenant = MagicMock()
    tenant.id = uuid.uuid4()
    tenant.stripe_customer_id = "cus_test"

    session = AsyncMock()
    empty_result = MagicMock()
    empty_result.scalar_one_or_none.return_value = None
    tenant_result = MagicMock()
    tenant_result.scalar_one_or_none.return_value = tenant
    session.execute.side_effect = [empty_result, tenant_result]

    inv_data = {
        "id": "in_paid",
        "customer": "cus_test",
        "status": "paid",
        "amount_due": 5000,
        "currency": "usd",
        "status_transitions": {"paid_at": 1700000000},
    }

    result = await sync_invoice(session, inv_data)

    assert result.paid_at is not None
    assert isinstance(result.paid_at, datetime)
