"""P6-02/03: Billing DB models and Tenant extension tests."""

import os
import uuid
from datetime import UTC, datetime

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

from aeo_api.billing.models import BillingEvent, Invoice, Subscription
from aeo_api.db.tenant_models import Tenant


def test_subscription_model_fields() -> None:
    sub = Subscription(
        tenant_id=uuid.uuid4(),
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test456",
        status="active",
        plan="pro",
    )
    assert sub.stripe_customer_id == "cus_test123"
    assert sub.stripe_subscription_id == "sub_test456"
    assert sub.status == "active"
    assert sub.plan == "pro"


def test_subscription_model_optional_fields() -> None:
    sub = Subscription(
        tenant_id=uuid.uuid4(),
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
    )
    assert sub.current_period_start is None
    assert sub.current_period_end is None
    assert sub.trial_start is None
    assert sub.trial_end is None
    assert sub.canceled_at is None
    assert sub.stripe_price_id is None
    assert sub.metadata_ is None


def test_subscription_model_period_dates() -> None:
    now = datetime.now(UTC)
    sub = Subscription(
        tenant_id=uuid.uuid4(),
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        current_period_start=now,
        current_period_end=now,
    )
    assert sub.current_period_start == now
    assert sub.current_period_end == now


def test_subscription_model_trial_dates() -> None:
    now = datetime.now(UTC)
    sub = Subscription(
        tenant_id=uuid.uuid4(),
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        trial_start=now,
        trial_end=now,
    )
    assert sub.trial_start == now
    assert sub.trial_end == now


def test_subscription_model_cancellation() -> None:
    now = datetime.now(UTC)
    sub = Subscription(
        tenant_id=uuid.uuid4(),
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        cancel_at_period_end=True,
        canceled_at=now,
    )
    assert sub.cancel_at_period_end is True
    assert sub.canceled_at == now


def test_subscription_model_metadata() -> None:
    sub = Subscription(
        tenant_id=uuid.uuid4(),
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        metadata_={"source": "web", "campaign": "launch"},
    )
    assert sub.metadata_ == {"source": "web", "campaign": "launch"}


def test_subscription_model_price_id() -> None:
    sub = Subscription(
        tenant_id=uuid.uuid4(),
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        stripe_price_id="price_pro_monthly",
    )
    assert sub.stripe_price_id == "price_pro_monthly"


def test_invoice_model_fields() -> None:
    inv = Invoice(
        tenant_id=uuid.uuid4(),
        stripe_invoice_id="in_test123",
        stripe_customer_id="cus_test456",
        status="paid",
        amount_due=2000,
        currency="usd",
    )
    assert inv.stripe_invoice_id == "in_test123"
    assert inv.stripe_customer_id == "cus_test456"
    assert inv.status == "paid"
    assert inv.amount_due == 2000
    assert inv.currency == "usd"


def test_invoice_model_optional_fields() -> None:
    inv = Invoice(
        tenant_id=uuid.uuid4(),
        stripe_invoice_id="in_test",
        stripe_customer_id="cus_test",
    )
    assert inv.stripe_subscription_id is None
    assert inv.paid_at is None
    assert inv.invoice_pdf is None
    assert inv.hosted_invoice_url is None
    assert inv.period_start is None
    assert inv.period_end is None


def test_invoice_model_subscription_link() -> None:
    inv = Invoice(
        tenant_id=uuid.uuid4(),
        stripe_invoice_id="in_test",
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
    )
    assert inv.stripe_subscription_id == "sub_test"


def test_invoice_model_period_dates() -> None:
    now = datetime.now(UTC)
    inv = Invoice(
        tenant_id=uuid.uuid4(),
        stripe_invoice_id="in_test",
        stripe_customer_id="cus_test",
        period_start=now,
        period_end=now,
    )
    assert inv.period_start == now
    assert inv.period_end == now


def test_invoice_model_payment() -> None:
    now = datetime.now(UTC)
    inv = Invoice(
        tenant_id=uuid.uuid4(),
        stripe_invoice_id="in_test",
        stripe_customer_id="cus_test",
        status="paid",
        paid_at=now,
        invoice_pdf="https://stripe.com/pdf/test",
        hosted_invoice_url="https://stripe.com/invoice/test",
    )
    assert inv.status == "paid"
    assert inv.paid_at == now
    assert inv.invoice_pdf == "https://stripe.com/pdf/test"
    assert inv.hosted_invoice_url == "https://stripe.com/invoice/test"


def test_invoice_model_amounts() -> None:
    inv = Invoice(
        tenant_id=uuid.uuid4(),
        stripe_invoice_id="in_test",
        stripe_customer_id="cus_test",
        amount_due=9900,
        currency="usd",
    )
    assert inv.amount_due == 9900
    assert inv.currency == "usd"


def test_billing_event_model_fields() -> None:
    event = BillingEvent(
        stripe_event_id="evt_test123",
        event_type="checkout.session.completed",
        stripe_customer_id="cus_test456",
        data={"object": {"id": "cs_test"}},
    )
    assert event.stripe_event_id == "evt_test123"
    assert event.event_type == "checkout.session.completed"
    assert event.stripe_customer_id == "cus_test456"
    assert event.data == {"object": {"id": "cs_test"}}


def test_billing_event_model_optional_fields() -> None:
    event = BillingEvent(
        stripe_event_id="evt_test",
        event_type="invoice.payment_succeeded",
    )
    assert event.stripe_customer_id is None
    assert event.data is None


def test_billing_event_model_processed() -> None:
    event = BillingEvent(
        stripe_event_id="evt_test",
        event_type="customer.subscription.updated",
        processed=True,
    )
    assert event.processed is True


def test_billing_event_model_no_customer() -> None:
    event = BillingEvent(
        stripe_event_id="evt_test",
        event_type="ping",
    )
    assert event.stripe_customer_id is None


def test_billing_event_model_data_payload() -> None:
    payload = {
        "object": {
            "id": "sub_test",
            "status": "active",
            "current_period_end": 1234567890,
        }
    }
    event = BillingEvent(
        stripe_event_id="evt_test",
        event_type="customer.subscription.updated",
        data=payload,
    )
    assert event.data == payload
    assert event.data["object"]["status"] == "active"


def test_tenant_model_billing_fields() -> None:
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        stripe_customer_id="cus_tenant123",
        billing_status="active",
    )
    assert tenant.stripe_customer_id == "cus_tenant123"
    assert tenant.billing_status == "active"
    assert tenant.trial_ends_at is None


def test_tenant_model_trial_ends() -> None:
    now = datetime.now(UTC)
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        trial_ends_at=now,
    )
    assert tenant.trial_ends_at == now


def test_tenant_model_billing_nullable() -> None:
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
    )
    assert tenant.stripe_customer_id is None
    assert tenant.trial_ends_at is None


def test_tenant_model_plan_still_exists() -> None:
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        plan="pro",
    )
    assert tenant.plan == "pro"


def test_tenant_model_all_billing_fields_together() -> None:
    now = datetime.now(UTC)
    tenant = Tenant(
        name="Full Billing Tenant",
        slug="full-billing",
        plan="enterprise",
        stripe_customer_id="cus_full123",
        trial_ends_at=now,
        billing_status="trialing",
    )
    assert tenant.plan == "enterprise"
    assert tenant.stripe_customer_id == "cus_full123"
    assert tenant.trial_ends_at == now
    assert tenant.billing_status == "trialing"


def test_tenant_model_existing_fields_unchanged() -> None:
    tenant = Tenant(
        name="Test",
        slug="test",
        plan="free",
        is_active=True,
    )
    assert tenant.name == "Test"
    assert tenant.slug == "test"
    assert tenant.plan == "free"
    assert tenant.is_active is True
