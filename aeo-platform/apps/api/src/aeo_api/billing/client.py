"""P6-01: Stripe client initialization and connectivity check."""

from typing import cast

import stripe
import structlog

from aeo_api.billing.config import BillingSettings, get_billing_settings

logger = structlog.get_logger(__name__)

_client_initialized = False


def init_stripe(settings: BillingSettings | None = None) -> None:
    global _client_initialized
    cfg = settings or get_billing_settings()
    if not cfg.api_key:
        logger.warning("stripe.not_configured", msg="STRIPE_API_KEY empty; billing disabled")
        return
    stripe.api_key = cfg.api_key
    stripe.max_network_retries = 2
    _client_initialized = True
    logger.info("stripe.initialized", api_version=stripe.api_version)


def is_stripe_enabled() -> bool:
    return _client_initialized and bool(get_billing_settings().api_key)


def verify_stripe_connectivity() -> dict[str, object]:
    """Lightweight health check: retrieve the Stripe account to confirm credentials work."""
    if not is_stripe_enabled():
        return {"stripe": "disabled", "ok": False, "reason": "no api_key configured"}
    try:
        account = stripe.Account.retrieve()
        return {
            "stripe": "connected",
            "ok": True,
            "account_id": account.id,
            "charges_enabled": getattr(account, "charges_enabled", False),
        }
    except stripe.AuthenticationError as exc:
        logger.error("stripe.auth_failed", error=str(exc))
        return {"stripe": "auth_failed", "ok": False, "reason": str(exc)}
    except stripe.StripeError as exc:
        logger.error("stripe.connection_error", error=str(exc))
        return {"stripe": "error", "ok": False, "reason": str(exc)}


def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
    """Validate and parse an incoming Stripe webhook event."""
    secret = get_billing_settings().webhook_secret
    if not secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
    return cast(stripe.Event, stripe.Webhook.construct_event(payload, sig_header, secret))
