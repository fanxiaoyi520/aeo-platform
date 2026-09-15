"""P6-21: Amazon credential API routes tests."""

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
from aeo_api.routers.amazon_credentials import (
    CredentialCreateRequest,
    CredentialMaskedResponse,
    CredentialTestRequest,
    _mask,
    _require_owner_admin,
)
from fastapi import HTTPException


def test_credential_create_request_schema() -> None:
    req = CredentialCreateRequest(
        client_id="test-client-id",
        client_secret="test-client-secret",
        refresh_token="test-refresh-token",
    )
    assert req.client_id == "test-client-id"
    assert req.marketplace_id == "ATVPDKIKX0DER"
    assert req.region == "us-east-1"


def test_credential_create_request_custom_marketplace() -> None:
    req = CredentialCreateRequest(
        client_id="id",
        client_secret="secret",
        refresh_token="token",
        marketplace_id="A1F83G8C2ARO7P",
        region="eu-west-1",
    )
    assert req.marketplace_id == "A1F83G8C2ARO7P"
    assert req.region == "eu-west-1"


def test_credential_test_request_with_id() -> None:
    cred_id = uuid.uuid4()
    req = CredentialTestRequest(credential_id=cred_id)
    assert req.credential_id == cred_id


def test_credential_test_request_with_inline_credentials() -> None:
    req = CredentialTestRequest(
        client_id="id",
        client_secret="secret",
        refresh_token="token",
    )
    assert req.client_id == "id"
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
        marketplace_id="ATVPDKIKX0DER",
        region="us-east-1",
        client_id_masked="test****",
        refresh_token_masked="refr****",
        is_active=True,
        created_at="2026-09-15T00:00:00+00:00",
        updated_at="2026-09-15T00:00:00+00:00",
    )
    assert resp.id == cred_id
    assert resp.is_active is True
