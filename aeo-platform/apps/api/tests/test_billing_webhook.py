"""P6-05: Stripe Webhook endpoint tests."""

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

import pytest
import stripe
from aeo_api.main import create_app
from aeo_api.routers.billing import HANDLED_EVENTS, _extract_event_data
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_handled_events_defined() -> None:
    assert "checkout.session.completed" in HANDLED_EVENTS
    assert "customer.subscription.updated" in HANDLED_EVENTS
    assert "customer.subscription.deleted" in HANDLED_EVENTS
    assert "invoice.payment_succeeded" in HANDLED_EVENTS
    assert "invoice.payment_failed" in HANDLED_EVENTS


def test_extract_event_data_from_dict() -> None:
    event = MagicMock()
    event.to_dict.return_value = {"type": "test", "data": {}}
    result = _extract_event_data(event)
    assert result == {"type": "test", "data": {}}


def test_extract_event_data_from_stripe_object() -> None:
    event = MagicMock(spec=[])
    event.data = MagicMock()
    event.data.object = {"id": "obj_test"}
    result = _extract_event_data(event)
    assert result == {"id": "obj_test"}


def test_extract_event_data_empty() -> None:
    event = MagicMock(spec=[])
    event.data = MagicMock(spec=[])
    result = _extract_event_data(event)
    assert result == {}


def test_webhook_invalid_signature(client: TestClient) -> None:
    with patch(
        "aeo_api.routers.billing.verify_webhook_signature",
        side_effect=ValueError("Invalid signature"),
    ):
        response = client.post(
            "/api/v1/billing/webhook",
            content=b'{"type":"test"}',
            headers={"Stripe-Signature": "invalid"},
        )
    assert response.status_code == 400
    body = response.json()
    assert "detail" in body or "message" in body


def test_webhook_stripe_signature_error(client: TestClient) -> None:
    with patch(
        "aeo_api.routers.billing.verify_webhook_signature",
        side_effect=stripe.SignatureVerificationError("Bad sig", "sig"),  # type: ignore[no-untyped-call]
    ):
        response = client.post(
            "/api/v1/billing/webhook",
            content=b'{"type":"test"}',
            headers={"Stripe-Signature": "invalid"},
        )
    assert response.status_code == 400


def test_webhook_ignored_event(client: TestClient) -> None:
    mock_event = MagicMock()
    mock_event.id = "evt_ignored"
    mock_event.type = "ping"

    with patch(
        "aeo_api.routers.billing.verify_webhook_signature",
        return_value=mock_event,
    ):
        response = client.post(
            "/api/v1/billing/webhook",
            content=b'{"type":"ping"}',
            headers={"Stripe-Signature": "valid_sig"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["received"] is True
    assert data["handled"] is False


def test_webhook_missing_signature_header(client: TestClient) -> None:
    response = client.post(
        "/api/v1/billing/webhook",
        content=b'{"type":"test"}',
    )
    assert response.status_code == 422
