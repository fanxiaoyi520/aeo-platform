"""P6-04: Billing service layer — Stripe Checkout, Portal, subscription sync."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import stripe
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.billing.config import BillingSettings, get_billing_settings
from aeo_api.billing.models import Invoice, Subscription
from aeo_api.db.tenant_models import Tenant

logger = structlog.get_logger(__name__)


class BillingServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _ts_from_stripe(stripe_ts: int | None) -> datetime | None:
    if stripe_ts is None:
        return None
    return datetime.fromtimestamp(stripe_ts, tz=timezone.utc)


async def create_checkout_session(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    price_id: str,
    settings: BillingSettings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_billing_settings()
    if not cfg.enabled:
        raise BillingServiceError("Billing not configured", status_code=503)

    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise BillingServiceError("Tenant not found", status_code=404)

    line_items = [{"price": price_id, "quantity": 1}]
    checkout_params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": line_items,
        "success_url": cfg.success_url,
        "cancel_url": cfg.cancel_url,
        "client_reference_id": str(tenant_id),
    }

    if tenant.stripe_customer_id:
        checkout_params["customer"] = tenant.stripe_customer_id
    else:
        checkout_params["customer_creation"] = "always"

    checkout_session = stripe.checkout.Session.create(**checkout_params)

    logger.info(
        "billing.checkout_created",
        tenant_id=str(tenant_id),
        session_id=checkout_session.id,
        price_id=price_id,
    )

    return {
        "checkout_url": checkout_session.url,
        "session_id": checkout_session.id,
    }


async def create_portal_session(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    return_url: str | None = None,
    settings: BillingSettings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_billing_settings()
    if not cfg.enabled:
        raise BillingServiceError("Billing not configured", status_code=503)

    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise BillingServiceError("Tenant not found", status_code=404)

    if not tenant.stripe_customer_id:
        raise BillingServiceError("Tenant has no Stripe customer", status_code=400)

    portal_session = stripe.billing_portal.Session.create(
        customer=tenant.stripe_customer_id,
        return_url=return_url or cfg.success_url,
    )

    logger.info(
        "billing.portal_created",
        tenant_id=str(tenant_id),
        session_id=portal_session.id,
    )

    return {
        "portal_url": portal_session.url,
    }


async def sync_subscription(
    session: AsyncSession,
    stripe_subscription: dict[str, Any] | Any,
) -> Subscription:
    if hasattr(stripe_subscription, "to_dict"):
        sub_data = stripe_subscription.to_dict()
    elif isinstance(stripe_subscription, dict):
        sub_data = stripe_subscription
    else:
        sub_data = dict(stripe_subscription)

    stripe_sub_id = sub_data.get("id")
    if not stripe_sub_id:
        raise BillingServiceError("Missing subscription id")

    result = await session.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_sub_id
        )
    )
    subscription = result.scalar_one_or_none()

    customer_id = sub_data.get("customer", "")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id", "")

    items = sub_data.get("items", {})
    if isinstance(items, dict):
        data_list = items.get("data", [])
    else:
        data_list = []
    price_id = ""
    if data_list:
        price_obj = data_list[0].get("price", {})
        price_id = price_obj.get("id", "") if isinstance(price_obj, dict) else ""

    plan = _extract_plan_from_price_id(price_id)

    if subscription is None:
        subscription = Subscription(
            tenant_id=_resolve_tenant_id(session, customer_id),
            stripe_customer_id=customer_id,
            stripe_subscription_id=stripe_sub_id,
        )
        session.add(subscription)

    subscription.stripe_customer_id = customer_id
    subscription.status = sub_data.get("status", "incomplete")
    subscription.stripe_price_id = price_id or None
    subscription.plan = plan
    subscription.current_period_start = _ts_from_stripe(sub_data.get("current_period_start"))
    subscription.current_period_end = _ts_from_stripe(sub_data.get("current_period_end"))
    subscription.trial_start = _ts_from_stripe(sub_data.get("trial_start"))
    subscription.trial_end = _ts_from_stripe(sub_data.get("trial_end"))
    subscription.cancel_at_period_end = sub_data.get("cancel_at_period_end", False)
    subscription.canceled_at = _ts_from_stripe(sub_data.get("canceled_at"))

    await session.flush()
    await session.refresh(subscription)

    logger.info(
        "billing.subscription_synced",
        subscription_id=stripe_sub_id,
        status=subscription.status,
        plan=plan,
    )

    return subscription


def _extract_plan_from_price_id(price_id: str) -> str:
    cfg = get_billing_settings()
    if price_id == cfg.price_pro_monthly:
        return "pro"
    if price_id == cfg.price_enterprise_monthly:
        return "enterprise"
    return "free"


async def _resolve_tenant_id(session: AsyncSession, stripe_customer_id: str) -> UUID:
    result = await session.execute(
        select(Tenant).where(Tenant.stripe_customer_id == stripe_customer_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is not None:
        return tenant.id
    raise BillingServiceError(
        f"Tenant not found for Stripe customer {stripe_customer_id}",
        status_code=404,
    )


async def handle_plan_change(
    session: AsyncSession,
    tenant_id: UUID,
    new_plan: str,
) -> Tenant:
    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise BillingServiceError("Tenant not found", status_code=404)

    old_plan = tenant.plan
    tenant.plan = new_plan
    await session.flush()
    await session.refresh(tenant)

    logger.info(
        "billing.plan_changed",
        tenant_id=str(tenant_id),
        old_plan=old_plan,
        new_plan=new_plan,
    )

    return tenant


async def sync_invoice(
    session: AsyncSession,
    stripe_invoice: dict[str, Any] | Any,
) -> Invoice:
    if hasattr(stripe_invoice, "to_dict"):
        inv_data = stripe_invoice.to_dict()
    elif isinstance(stripe_invoice, dict):
        inv_data = stripe_invoice
    else:
        inv_data = dict(stripe_invoice)

    stripe_inv_id = inv_data.get("id")
    if not stripe_inv_id:
        raise BillingServiceError("Missing invoice id")

    result = await session.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == stripe_inv_id)
    )
    invoice = result.scalar_one_or_none()

    customer_id = inv_data.get("customer", "")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id", "")

    subscription_id = inv_data.get("subscription")
    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")

    if invoice is None:
        invoice = Invoice(
            tenant_id=_resolve_tenant_id(session, customer_id),
            stripe_invoice_id=stripe_inv_id,
            stripe_customer_id=customer_id,
        )
        session.add(invoice)

    invoice.stripe_customer_id = customer_id
    invoice.stripe_subscription_id = subscription_id
    invoice.status = inv_data.get("status", "draft")
    invoice.amount_due = inv_data.get("amount_due", 0)
    invoice.currency = inv_data.get("currency", "usd")
    invoice.period_start = _ts_from_stripe(inv_data.get("period_start"))
    invoice.period_end = _ts_from_stripe(inv_data.get("period_end"))
    invoice.paid_at = _ts_from_stripe(inv_data.get("status_transitions", {}).get("paid_at"))
    invoice.invoice_pdf = inv_data.get("invoice_pdf")
    invoice.hosted_invoice_url = inv_data.get("hosted_invoice_url")

    await session.flush()
    await session.refresh(invoice)

    logger.info(
        "billing.invoice_synced",
        invoice_id=stripe_inv_id,
        status=invoice.status,
        amount=invoice.amount_due,
    )

    return invoice
