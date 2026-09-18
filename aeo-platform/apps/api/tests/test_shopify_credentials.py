"""P6-26: Shopify credential API routes tests."""

import os
import uuid

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

import pytest
from aeo_api.routers.shopify_credentials import (
    CredentialCreateRequest,
    CredentialMaskedResponse,
    CredentialTestRequest,
    _mask,
    _require_owner_admin,
)
from fastapi import HTTPException


def test_credential_create_request_schema() -> None:
    req = CredentialCreateRequest(
        store_url="https://test-store.myshopify.com",
        access_token="shpat_test_token",
    )
    assert req.store_url == "https://test-store.myshopify.com"
    assert req.access_token == "shpat_test_token"
    assert req.shop_name == ""


def test_credential_create_request_with_shop_name() -> None:
    req = CredentialCreateRequest(
        store_url="https://test-store.myshopify.com",
        access_token="shpat_test_token",
        shop_name="Test Store",
    )
    assert req.shop_name == "Test Store"


def test_credential_test_request_with_id() -> None:
    cred_id = uuid.uuid4()
    req = CredentialTestRequest(credential_id=cred_id)
    assert req.credential_id == cred_id


def test_credential_test_request_with_inline_credentials() -> None:
    req = CredentialTestRequest(
        store_url="https://test-store.myshopify.com",
        access_token="shpat_test_token",
    )
    assert req.store_url == "https://test-store.myshopify.com"
    assert req.access_token == "shpat_test_token"
    assert req.credential_id is None


def test_mask_short_string() -> None:
    assert _mask("abc") == "****"
    assert _mask("abcd") == "****"


def test_mask_long_string() -> None:
    result = _mask("abcdefghij")
    assert result == "abcd******"
    assert len(result) == 10


def test_require_owner_admin_owner() -> None:
    _require_owner_admin("owner")


def test_require_owner_admin_admin() -> None:
    _require_owner_admin("admin")


def test_require_owner_admin_member_raises() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _require_owner_admin("member")
    assert exc_info.value.status_code == 403


def test_credential_masked_response_schema() -> None:
    cred_id = uuid.uuid4()
    resp = CredentialMaskedResponse(
        id=cred_id,
        shop_name="Test Store",
        store_url_masked="http****",
        access_token_masked="shpa****",
        is_active=True,
        created_at="2026-09-15T00:00:00+00:00",
        updated_at="2026-09-15T00:00:00+00:00",
    )
    assert resp.id == cred_id
    assert resp.shop_name == "Test Store"
    assert resp.is_active is True


def test_required_scopes_logic() -> None:
    required_scopes = {"read_products", "read_orders", "read_customers"}
    granted = ["read_products", "read_orders", "read_customers", "read_inventory"]
    missing = required_scopes - set(granted)
    assert len(missing) == 0


def test_missing_scopes_logic() -> None:
    required_scopes = {"read_products", "read_orders", "read_customers"}
    granted = ["read_products"]
    missing = required_scopes - set(granted)
    assert missing == {"read_orders", "read_customers"}
    assert sorted(missing) == ["read_customers", "read_orders"]
