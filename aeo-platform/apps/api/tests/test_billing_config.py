"""P6-01: Stripe billing configuration and client tests."""

import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

import stripe
from aeo_api.billing.client import (
    init_stripe,
    is_stripe_enabled,
    verify_stripe_connectivity,
    verify_webhook_signature,
)
from aeo_api.billing.config import BillingSettings, get_billing_settings


def test_billing_settings_defaults() -> None:
    settings = BillingSettings()
    assert settings.api_key == ""
    assert settings.webhook_secret == ""
    assert settings.trial_days == 14
    assert settings.enabled is False


def test_billing_settings_enabled_with_key() -> None:
    settings = BillingSettings(api_key="sk_test_123")
    assert settings.enabled is True


def test_billing_settings_env_prefix() -> None:
    env = {"STRIPE_API_KEY": "sk_test_env", "STRIPE_WEBHOOK_SECRET": "whsec_env"}
    with patch.dict(os.environ, env):
        settings = BillingSettings()
        assert settings.api_key == "sk_test_env"
        assert settings.webhook_secret == "whsec_env"


def test_get_billing_settings_cached() -> None:
    get_billing_settings.cache_clear()
    s1 = get_billing_settings()
    s2 = get_billing_settings()
    assert s1 is s2
    get_billing_settings.cache_clear()


def test_init_stripe_no_key_disables() -> None:
    import aeo_api.billing.client as client_mod

    client_mod._client_initialized = False
    settings = BillingSettings(api_key="")
    init_stripe(settings)
    assert is_stripe_enabled() is False


def test_init_stripe_with_key_enables() -> None:
    import aeo_api.billing.client as client_mod

    client_mod._client_initialized = False
    settings = BillingSettings(api_key="sk_test_init")
    with patch.object(get_billing_settings, "__wrapped__", return_value=settings):
        get_billing_settings.cache_clear()
        with patch("aeo_api.billing.client.get_billing_settings", return_value=settings):
            init_stripe(settings)
            assert client_mod._client_initialized is True
            assert stripe.api_key == "sk_test_init"
    client_mod._client_initialized = False
    get_billing_settings.cache_clear()


def test_verify_connectivity_disabled() -> None:
    import aeo_api.billing.client as client_mod

    client_mod._client_initialized = False
    result = verify_stripe_connectivity()
    assert result["ok"] is False
    assert result["stripe"] == "disabled"


def test_verify_connectivity_success() -> None:
    import aeo_api.billing.client as client_mod

    client_mod._client_initialized = True
    settings = BillingSettings(api_key="sk_test_conn")
    mock_account = MagicMock()
    mock_account.id = "acct_123"
    mock_account.charges_enabled = True
    with (
        patch("aeo_api.billing.client.get_billing_settings", return_value=settings),
        patch("aeo_api.billing.client.stripe.Account.retrieve", return_value=mock_account),
    ):
        result = verify_stripe_connectivity()
        assert result["ok"] is True
        assert result["account_id"] == "acct_123"
        assert result["charges_enabled"] is True
    client_mod._client_initialized = False


def test_verify_connectivity_auth_error() -> None:
    import aeo_api.billing.client as client_mod

    client_mod._client_initialized = True
    settings = BillingSettings(api_key="sk_test_bad")
    with (
        patch("aeo_api.billing.client.get_billing_settings", return_value=settings),
        patch(
            "aeo_api.billing.client.stripe.Account.retrieve",
            side_effect=stripe.AuthenticationError("Invalid API Key"),
        ),
    ):
        result = verify_stripe_connectivity()
        assert result["ok"] is False
        assert result["stripe"] == "auth_failed"
    client_mod._client_initialized = False


def test_verify_webhook_signature_no_secret() -> None:
    settings = BillingSettings(webhook_secret="")
    with patch("aeo_api.billing.client.get_billing_settings", return_value=settings):
        try:
            verify_webhook_signature(b"{}", "sig")
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "not configured" in str(exc)


def test_verify_webhook_signature_valid() -> None:
    settings = BillingSettings(webhook_secret="whsec_test")
    mock_event = MagicMock()
    with (
        patch("aeo_api.billing.client.get_billing_settings", return_value=settings),
        patch(
            "aeo_api.billing.client.stripe.Webhook.construct_event",
            return_value=mock_event,
        ) as mock_construct,
    ):
        result = verify_webhook_signature(b'{"type":"ping"}', "t=1,v1=abc")
        assert result is mock_event
        mock_construct.assert_called_once_with(b'{"type":"ping"}', "t=1,v1=abc", "whsec_test")
