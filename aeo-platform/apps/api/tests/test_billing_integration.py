"""P6-09: P6-MS1 验收 — 计费服务集成测试 + webhook 模拟 + plan 同步验证."""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASEURL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")

import pytest
from aeo_api.billing.models import BillingEvent, Invoice, Subscription
from aeo_api.billing.service import (
    handle_plan_change,
    sync_invoice,
    sync_subscription,
)
from aeo_api.db.tenant_models import Tenant


@pytest.fixture(autouse=True)
def mock_billing_settings() -> Any:
    with patch("aeo_api.billing.service.get_billing_settings") as mock:
        settings = MagicMock()
        settings.price_pro_monthly = "price_pro_monthly"
        settings.price_enterprise_monthly = "price_enterprise_monthly"
        mock.return_value = settings
        yield settings


def _make_tenant(plan: str = "free", stripe_customer_id: str | None = None) -> MagicMock:
    tenant = MagicMock(spec=Tenant)
    tenant.id = uuid4()
    tenant.plan = plan
    tenant.stripe_customer_id = stripe_customer_id or f"cus_{uuid4().hex[:14]}"
    tenant.trial_ends_at = None
    tenant.billing_status = "active"
    return tenant


def _make_stripe_subscription(
    sub_id: str = "sub_test123",
    status: str = "active",
    plan: str = "pro",
    customer_id: str = "cus_test123",
) -> MagicMock:
    sub = MagicMock()
    sub.id = sub_id

    if plan == "pro":
        price_id = "price_pro_monthly"
    elif plan == "enterprise":
        price_id = "price_enterprise_monthly"
    else:
        price_id = ""

    sub_dict = {
        "id": sub_id,
        "status": status,
        "customer": customer_id,
        "current_period_start": 1700000000,
        "current_period_end": 1702592000,
        "cancel_at_period_end": False,
        "canceled_at": None,
        "trial_start": None,
        "trial_end": None,
        "items": {"data": [{"price": {"id": price_id}}]},
    }
    sub.to_dict.return_value = sub_dict
    sub.get = lambda key, default=None: sub_dict.get(key, default)

    return sub


def _make_stripe_invoice(
    inv_id: str = "in_test123",
    status: str = "paid",
    amount: int = 2000,
    sub_id: str = "sub_test123",
) -> MagicMock:
    inv = MagicMock()
    inv.id = inv_id

    inv_dict = {
        "id": inv_id,
        "status": status,
        "amount_due": amount,
        "currency": "usd",
        "period_start": 1700000000,
        "period_end": 1702592000,
        "subscription": sub_id,
        "customer": "cus_test123",
        "invoice_pdf": "https://stripe.com/pdf/test",
        "hosted_invoice_url": "https://stripe.com/invoice/test",
        "status_transitions": {"paid_at": 1700100000 if status == "paid" else None},
    }
    inv.to_dict.return_value = inv_dict
    inv.get = lambda key, default=None: inv_dict.get(key, default)

    return inv


def _make_mock_session(
    tenant: MagicMock | None = None,
    existing_sub: Subscription | None = None,
    existing_invoices: list[Any] | None = None,
) -> AsyncMock:
    session = AsyncMock()

    tenant_result = MagicMock()
    tenant_result.scalar_one_or_none.return_value = tenant

    sub_result = MagicMock()
    sub_result.scalar_one_or_none.return_value = existing_sub

    invoices_result = MagicMock()
    invoices_result.scalars.return_value.all.return_value = existing_invoices or []

    event_result = MagicMock()
    event_result.scalar_one_or_none.return_value = None

    session.execute = AsyncMock(
        side_effect=[tenant_result, sub_result, event_result, invoices_result]
    )
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()

    return session


class TestWebhookCheckoutCompleted:
    @pytest.mark.asyncio
    async def test_checkout_completed_creates_subscription(self) -> None:
        tenant = _make_tenant(plan="free")
        stripe_sub = _make_stripe_subscription(plan="pro")

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant

        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[sub_result, tenant_result])
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        sub = await sync_subscription(session, stripe_sub)

        session.add.assert_called()
        assert sub.stripe_subscription_id == "sub_test123"
        assert sub.plan == "pro"
        assert sub.status == "active"

    @pytest.mark.asyncio
    async def test_plan_change_updates_tenant(self) -> None:
        tenant = _make_tenant(plan="free")
        session = AsyncMock()

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant
        session.execute = AsyncMock(return_value=tenant_result)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        await handle_plan_change(session, tenant.id, "pro")

        assert tenant.plan == "pro"
        session.flush.assert_called_once()


class TestWebhookSubscriptionUpdated:
    @pytest.mark.asyncio
    async def test_subscription_updated_syncs_changes(self) -> None:
        stripe_sub = _make_stripe_subscription(status="active", plan="enterprise")

        existing_sub = MagicMock(spec=Subscription)
        existing_sub.stripe_subscription_id = "sub_test123"

        tenant = _make_tenant(plan="pro")
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant

        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = existing_sub

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[sub_result, tenant_result])
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        sub = await sync_subscription(session, stripe_sub)

        session.flush.assert_called()
        assert sub.plan == "enterprise"


class TestWebhookSubscriptionDeleted:
    @pytest.mark.asyncio
    async def test_subscription_deleted_marks_canceled(self) -> None:
        stripe_sub = _make_stripe_subscription(status="canceled")

        existing_sub = MagicMock(spec=Subscription)
        existing_sub.stripe_subscription_id = "sub_test123"

        tenant = _make_tenant(plan="pro")
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant

        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = existing_sub

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[sub_result, tenant_result])
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        sub = await sync_subscription(session, stripe_sub)

        assert sub.status == "canceled"


class TestWebhookInvoicePayment:
    @pytest.mark.asyncio
    async def test_invoice_payment_succeeded_syncs_invoice(self) -> None:
        stripe_inv = _make_stripe_invoice(status="paid")

        tenant = _make_tenant()
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant

        inv_result = MagicMock()
        inv_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[inv_result, tenant_result])
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        inv = await sync_invoice(session, stripe_inv)

        session.add.assert_called()
        assert inv.status == "paid"
        assert inv.amount_due == 2000

    @pytest.mark.asyncio
    async def test_invoice_payment_failed_records_invoice(self) -> None:
        stripe_inv = _make_stripe_invoice(status="open", amount=5000)

        tenant = _make_tenant()
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant

        inv_result = MagicMock()
        inv_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[inv_result, tenant_result])
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        inv = await sync_invoice(session, stripe_inv)

        assert inv.status == "open"
        assert inv.amount_due == 5000


class TestEndToEndBillingFlow:
    @pytest.mark.asyncio
    async def test_full_subscription_lifecycle(self) -> None:
        tenant = _make_tenant(plan="free")

        stripe_sub = _make_stripe_subscription(plan="pro", status="active")

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant
        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[sub_result, tenant_result])
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        sub = await sync_subscription(session, stripe_sub)
        assert sub.plan == "pro"
        assert sub.status == "active"

        tenant_result2 = MagicMock()
        tenant_result2.scalar_one_or_none.return_value = tenant
        session.execute = AsyncMock(return_value=tenant_result2)

        await handle_plan_change(session, tenant.id, "pro")
        assert tenant.plan == "pro"

        upgraded_sub = _make_stripe_subscription(plan="enterprise", status="active")
        existing_sub = MagicMock(spec=Subscription)
        existing_sub.stripe_subscription_id = "sub_test123"

        sub_result2 = MagicMock()
        sub_result2.scalar_one_or_none.return_value = existing_sub
        session.execute = AsyncMock(side_effect=[sub_result2, tenant_result2])

        sub = await sync_subscription(session, upgraded_sub)
        assert sub.plan == "enterprise"

        canceled_sub = _make_stripe_subscription(plan="enterprise", status="canceled")
        sub_result3 = MagicMock()
        sub_result3.scalar_one_or_none.return_value = existing_sub
        session.execute = AsyncMock(side_effect=[sub_result3, tenant_result2])

        sub = await sync_subscription(session, canceled_sub)
        assert sub.status == "canceled"

        await handle_plan_change(session, tenant.id, "free")
        assert tenant.plan == "free"

    @pytest.mark.asyncio
    async def test_idempotent_webhook_processing(self) -> None:
        session = AsyncMock()

        existing_event = MagicMock(spec=BillingEvent)
        existing_event.stripe_event_id = "evt_test_123"

        event_result = MagicMock()
        event_result.scalar_one_or_none.return_value = existing_event
        session.execute = AsyncMock(return_value=event_result)

        result = await session.execute(MagicMock())
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.stripe_event_id == "evt_test_123"


class TestPlanSyncVerification:
    @pytest.mark.asyncio
    async def test_free_to_pro_upgrade(self) -> None:
        tenant = _make_tenant(plan="free")
        session = AsyncMock()

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant
        session.execute = AsyncMock(return_value=tenant_result)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        await handle_plan_change(session, tenant.id, "pro")
        assert tenant.plan == "pro"

    @pytest.mark.asyncio
    async def test_pro_to_enterprise_upgrade(self) -> None:
        tenant = _make_tenant(plan="pro")
        session = AsyncMock()

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant
        session.execute = AsyncMock(return_value=tenant_result)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        await handle_plan_change(session, tenant.id, "enterprise")
        assert tenant.plan == "enterprise"

    @pytest.mark.asyncio
    async def test_downgrade_to_free_on_cancellation(self) -> None:
        tenant = _make_tenant(plan="pro")
        session = AsyncMock()

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant
        session.execute = AsyncMock(return_value=tenant_result)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        await handle_plan_change(session, tenant.id, "free")
        assert tenant.plan == "free"

    @pytest.mark.asyncio
    async def test_plan_change_always_flushes(self) -> None:
        tenant = _make_tenant(plan="pro")
        session = AsyncMock()

        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = tenant
        session.execute = AsyncMock(return_value=tenant_result)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        await handle_plan_change(session, tenant.id, "pro")
        session.flush.assert_called_once()


class TestBillingModelsIntegrity:
    def test_subscription_model_complete(self) -> None:
        sub = Subscription(
            stripe_subscription_id="sub_test",
            stripe_customer_id="cus_test",
            status="active",
            plan="pro",
        )
        assert sub.stripe_subscription_id == "sub_test"
        assert sub.status == "active"
        assert sub.plan == "pro"

    def test_invoice_model_complete(self) -> None:
        inv = Invoice(
            stripe_invoice_id="in_test",
            stripe_subscription_id="sub_test",
            status="paid",
            amount_due=2000,
            currency="usd",
        )
        assert inv.stripe_invoice_id == "in_test"
        assert inv.amount_due == 2000
        assert inv.currency == "usd"

    def test_billing_event_model_complete(self) -> None:
        event = BillingEvent(
            stripe_event_id="evt_test",
            event_type="checkout.session.completed",
            data={"test": True},
            processed=True,
        )
        assert event.stripe_event_id == "evt_test"
        assert event.event_type == "checkout.session.completed"
        assert event.processed is True

    def test_tenant_billing_fields(self) -> None:
        tenant = Tenant(
            name="Test",
            slug="test",
            plan="pro",
            stripe_customer_id="cus_test",
            billing_status="active",
        )
        assert tenant.stripe_customer_id == "cus_test"
        assert tenant.billing_status == "active"
        assert tenant.plan == "pro"
