"""P6-06: Billing API routes tests."""

import os
import uuid
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
from aeo_api.routers.billing import CheckoutRequest, PortalRequest, _require_owner_or_admin


def test_checkout_request_schema() -> None:
    req = CheckoutRequest(price_id="price_pro_monthly")
    assert req.price_id == "price_pro_monthly"


def test_portal_request_schema() -> None:
    req = PortalRequest(return_url="https://example.com/success")
    assert req.return_url == "https://example.com/success"


def test_portal_request_optional_return_url() -> None:
    req = PortalRequest()
    assert req.return_url is None


def test_require_owner_or_admin_owner() -> None:
    _require_owner_or_admin("owner")


def test_require_owner_or_admin_admin() -> None:
    _require_owner_or_admin("admin")


def test_require_owner_or_admin_member_raises() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        _require_owner_or_admin("member")
    assert exc_info.value.status_code == 403


def test_require_owner_or_admin_viewer_raises() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        _require_owner_or_admin("viewer")
    assert exc_info.value.status_code == 403


def test_require_owner_or_admin_empty_raises() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        _require_owner_or_admin("")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_checkout_calls_service() -> None:
    from aeo_api.routers.billing import checkout

    mock_session = AsyncMock()
    tenant_id = str(uuid.uuid4())

    with (
        patch("aeo_api.routers.billing.create_checkout_session") as mock_create,
    ):
        mock_create.return_value = {"checkout_url": "https://test.com", "session_id": "cs_test"}

        result = await checkout(
            tenant_id=tenant_id,
            role="owner",
            body=CheckoutRequest(price_id="price_pro"),
            session=mock_session,
        )

    assert result["checkout_url"] == "https://test.com"
    assert result["session_id"] == "cs_test"
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_portal_calls_service() -> None:
    from aeo_api.routers.billing import portal

    mock_session = AsyncMock()
    tenant_id = str(uuid.uuid4())

    with (
        patch("aeo_api.routers.billing.create_portal_session") as mock_create,
    ):
        mock_create.return_value = {"portal_url": "https://portal.test.com"}

        result = await portal(
            tenant_id=tenant_id,
            role="admin",
            body=PortalRequest(return_url="https://return.com"),
            session=mock_session,
        )

    assert result["portal_url"] == "https://portal.test.com"
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_portal_no_body() -> None:
    from aeo_api.routers.billing import portal

    mock_session = AsyncMock()
    tenant_id = str(uuid.uuid4())

    with (
        patch("aeo_api.routers.billing.create_portal_session") as mock_create,
    ):
        mock_create.return_value = {"portal_url": "https://portal.test.com"}

        result = await portal(
            tenant_id=tenant_id,
            role="owner",
            body=None,
            session=mock_session,
        )

    assert result["portal_url"] == "https://portal.test.com"


@pytest.mark.asyncio
async def test_get_subscription_none() -> None:
    from aeo_api.routers.billing import get_subscription

    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = result_mock

    result = await get_subscription(
        tenant_id=str(uuid.uuid4()),
        role="owner",
        session=mock_session,
    )

    assert result["has_subscription"] is False
    assert result["subscription"] is None


@pytest.mark.asyncio
async def test_get_subscription_exists() -> None:
    from aeo_api.routers.billing import get_subscription

    mock_sub = MagicMock()
    mock_sub.id = uuid.uuid4()
    mock_sub.stripe_subscription_id = "sub_test"
    mock_sub.status = "active"
    mock_sub.plan = "pro"
    mock_sub.current_period_start = None
    mock_sub.current_period_end = None
    mock_sub.cancel_at_period_end = False

    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_sub
    mock_session.execute.return_value = result_mock

    result = await get_subscription(
        tenant_id=str(uuid.uuid4()),
        role="owner",
        session=mock_session,
    )

    assert result["has_subscription"] is True
    assert result["subscription"]["status"] == "active"
    assert result["subscription"]["plan"] == "pro"


@pytest.mark.asyncio
async def test_list_invoices_empty() -> None:
    from aeo_api.routers.billing import list_invoices

    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = result_mock

    result = await list_invoices(
        tenant_id=str(uuid.uuid4()),
        role="owner",
        session=mock_session,
    )

    assert result["total"] == 0
    assert result["items"] == []


@pytest.mark.asyncio
async def test_list_invoices_with_items() -> None:
    from aeo_api.routers.billing import list_invoices

    mock_inv = MagicMock()
    mock_inv.id = uuid.uuid4()
    mock_inv.stripe_invoice_id = "in_test"
    mock_inv.status = "paid"
    mock_inv.amount_due = 2000
    mock_inv.currency = "usd"
    mock_inv.period_start = None
    mock_inv.period_end = None
    mock_inv.paid_at = None
    mock_inv.invoice_pdf = None
    mock_inv.hosted_invoice_url = None

    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_inv]
    mock_session.execute.return_value = result_mock

    result = await list_invoices(
        tenant_id=str(uuid.uuid4()),
        role="owner",
        session=mock_session,
    )

    assert result["total"] == 1
    assert result["items"][0]["stripe_invoice_id"] == "in_test"
    assert result["items"][0]["status"] == "paid"
    assert result["items"][0]["amount_due"] == 2000


@pytest.mark.asyncio
async def test_checkout_service_error() -> None:
    from aeo_api.billing.service import BillingServiceError
    from aeo_api.routers.billing import checkout

    mock_session = AsyncMock()

    with (
        patch(
            "aeo_api.routers.billing.create_checkout_session",
            side_effect=BillingServiceError("Billing not configured", status_code=503),
        ),
        pytest.raises(Exception) as exc_info,
    ):
        await checkout(
            tenant_id=str(uuid.uuid4()),
            role="owner",
            body=CheckoutRequest(price_id="price_test"),
            session=mock_session,
        )

    assert exc_info.value.status_code == 503  # type: ignore[attr-defined]
