"""P6-05/06: Stripe Webhook endpoint and billing API routes."""

from typing import Any
from uuid import UUID

import stripe
import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.auth.rbac import CurrentRole, CurrentTenant
from aeo_api.billing.client import verify_webhook_signature
from aeo_api.billing.models import BillingEvent, Invoice, Subscription
from aeo_api.billing.service import (
    BillingServiceError,
    create_checkout_session,
    create_portal_session,
    handle_plan_change,
    sync_invoice,
    sync_subscription,
)
from aeo_api.db.models import get_db_session
from aeo_api.db.tenant_models import Tenant

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

HANDLED_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    payload = await request.body()

    try:
        event = verify_webhook_signature(payload, stripe_signature)
    except ValueError as exc:
        logger.warning("webhook.signature_invalid", error=str(exc))
        raise HTTPException(status_code=400, detail="Invalid signature")
    except stripe.SignatureVerificationError as exc:
        logger.warning("webhook.signature_invalid", error=str(exc))
        raise HTTPException(status_code=400, detail="Invalid signature")
    except stripe.StripeError as exc:
        logger.error("webhook.stripe_error", error=str(exc))
        raise HTTPException(status_code=400, detail="Webhook verification failed")

    event_id = event.id
    event_type = event.type

    if event_type not in HANDLED_EVENTS:
        logger.info("webhook.event_ignored", event_id=event_id, event_type=event_type)
        return {"received": True, "handled": False}

    existing = await session.execute(
        select(BillingEvent).where(BillingEvent.stripe_event_id == event_id)
    )
    if existing.scalar_one_or_none() is not None:
        logger.info("webhook.event_duplicate", event_id=event_id)
        return {"received": True, "handled": False, "duplicate": True}

    billing_event = BillingEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        data=_extract_event_data(event),
    )
    session.add(billing_event)

    try:
        await _process_event(session, event_type, event.data.object)
        billing_event.processed = True
        if hasattr(event.data.object, "get"):
            customer = event.data.object.get("customer")
        elif hasattr(event.data.object, "customer"):
            customer = event.data.object.customer
        else:
            customer = None
        if customer:
            billing_event.stripe_customer_id = customer if isinstance(customer, str) else None
    except BillingServiceError as exc:
        logger.error(
            "webhook.processing_failed",
            event_id=event_id,
            event_type=event_type,
            error=exc.message,
        )
        raise HTTPException(status_code=400, detail=exc.message)

    await session.commit()

    logger.info("webhook.event_processed", event_id=event_id, event_type=event_type)
    return {"received": True, "handled": True}


def _extract_event_data(event: Any) -> dict[str, Any]:
    if hasattr(event, "to_dict"):
        return event.to_dict()
    if hasattr(event, "data") and hasattr(event.data, "object"):
        obj = event.data.object
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if isinstance(obj, dict):
            return obj
    return {}


async def _process_event(
    session: AsyncSession,
    event_type: str,
    event_object: Any,
) -> None:
    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(session, event_object)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(session, event_object)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(session, event_object)
    elif event_type == "invoice.payment_succeeded":
        await _handle_invoice_payment_succeeded(session, event_object)
    elif event_type == "invoice.payment_failed":
        await _handle_invoice_payment_failed(session, event_object)


async def _handle_checkout_completed(session: AsyncSession, checkout_session: Any) -> None:
    if hasattr(checkout_session, "get"):
        subscription_id = checkout_session.get("subscription")
        customer_id = checkout_session.get("customer")
        client_ref = checkout_session.get("client_reference_id")
    else:
        subscription_id = getattr(checkout_session, "subscription", None)
        customer_id = getattr(checkout_session, "customer", None)
        client_ref = getattr(checkout_session, "client_reference_id", None)

    if not subscription_id:
        logger.info("webhook.checkout_no_subscription")
        return

    try:
        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        subscription = await sync_subscription(session, stripe_sub)

        if client_ref and not subscription.tenant_id:
            from uuid import UUID
            result = await session.execute(
                select(Tenant).where(Tenant.stripe_customer_id == customer_id)
            )
            tenant = result.scalar_one_or_none()
            if tenant:
                subscription.tenant_id = tenant.id

        result = await session.execute(select(Tenant).where(Tenant.id == subscription.tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant and tenant.plan != subscription.plan:
            await handle_plan_change(session, tenant.id, subscription.plan)

    except Exception as exc:
        logger.error("webhook.checkout_sync_failed", error=str(exc))
        raise BillingServiceError(f"Failed to sync subscription: {exc}")


async def _handle_subscription_updated(session: AsyncSession, subscription_obj: Any) -> None:
    try:
        subscription = await sync_subscription(session, subscription_obj)

        result = await session.execute(select(Tenant).where(Tenant.id == subscription.tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant and tenant.plan != subscription.plan:
            await handle_plan_change(session, tenant.id, subscription.plan)

    except Exception as exc:
        logger.error("webhook.subscription_sync_failed", error=str(exc))
        raise BillingServiceError(f"Failed to sync subscription: {exc}")


async def _handle_subscription_deleted(session: AsyncSession, subscription_obj: Any) -> None:
    try:
        subscription = await sync_subscription(session, subscription_obj)

        result = await session.execute(select(Tenant).where(Tenant.id == subscription.tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant and tenant.plan != "free":
            await handle_plan_change(session, tenant.id, "free")

    except Exception as exc:
        logger.error("webhook.subscription_delete_failed", error=str(exc))
        raise BillingServiceError(f"Failed to handle subscription deletion: {exc}")


async def _handle_invoice_payment_succeeded(session: AsyncSession, invoice_obj: Any) -> None:
    try:
        await sync_invoice(session, invoice_obj)
    except Exception as exc:
        logger.error("webhook.invoice_sync_failed", error=str(exc))
        raise BillingServiceError(f"Failed to sync invoice: {exc}")


async def _handle_invoice_payment_failed(session: AsyncSession, invoice_obj: Any) -> None:
    try:
        await sync_invoice(session, invoice_obj)
        logger.warning(
            "webhook.invoice_payment_failed",
            invoice_id=invoice_obj.get("id") if hasattr(invoice_obj, "get") else getattr(invoice_obj, "id", None),
        )
    except Exception as exc:
        logger.error("webhook.invoice_sync_failed", error=str(exc))
        raise BillingServiceError(f"Failed to sync invoice: {exc}")


class CheckoutRequest(BaseModel):
    price_id: str


class PortalRequest(BaseModel):
    return_url: str | None = None


def _require_owner_or_admin(role: str) -> None:
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Owner or admin role required")


@router.post("/checkout")
async def checkout(
    tenant_id: CurrentTenant,
    role: CurrentRole,
    body: CheckoutRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    _require_owner_or_admin(role)
    try:
        result = await create_checkout_session(
            session, UUID(tenant_id), price_id=body.price_id
        )
        return result
    except BillingServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/portal")
async def portal(
    tenant_id: CurrentTenant,
    role: CurrentRole,
    body: PortalRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    _require_owner_or_admin(role)
    try:
        result = await create_portal_session(
            session, UUID(tenant_id), return_url=body.return_url if body else None
        )
        return result
    except BillingServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/subscription")
async def get_subscription(
    tenant_id: CurrentTenant,
    role: CurrentRole,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    _require_owner_or_admin(role)
    result = await session.execute(
        select(Subscription).where(Subscription.tenant_id == UUID(tenant_id))
    )
    subscription = result.scalar_one_or_none()

    if subscription is None:
        return {"has_subscription": False, "subscription": None}

    return {
        "has_subscription": True,
        "subscription": {
            "id": str(subscription.id),
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "status": subscription.status,
            "plan": subscription.plan,
            "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        },
    }


@router.get("/invoices")
async def list_invoices(
    tenant_id: CurrentTenant,
    role: CurrentRole,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    _require_owner_or_admin(role)
    result = await session.execute(
        select(Invoice)
        .where(Invoice.tenant_id == UUID(tenant_id))
        .order_by(Invoice.created_at.desc())
    )
    invoices = result.scalars().all()

    return {
        "items": [
            {
                "id": str(inv.id),
                "stripe_invoice_id": inv.stripe_invoice_id,
                "status": inv.status,
                "amount_due": inv.amount_due,
                "currency": inv.currency,
                "period_start": inv.period_start.isoformat() if inv.period_start else None,
                "period_end": inv.period_end.isoformat() if inv.period_end else None,
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url,
            }
            for inv in invoices
        ],
        "total": len(invoices),
    }
