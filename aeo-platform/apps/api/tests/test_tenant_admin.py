"""P5-07: Tenant admin schemas and service unit tests."""

import os
from uuid import uuid4

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASEURL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")

import pytest
from aeo_api.auth.tenant_service import TenantServiceError
from aeo_api.schemas.tenant import (
    InviteMemberRequest,
    TenantMemberResponse,
    TenantResponse,
    TenantUpdateRequest,
    UpdateMemberRoleRequest,
)
from pydantic import ValidationError


class TestTenantSchemas:
    def test_tenant_response_schema(self) -> None:
        resp = TenantResponse(
            id=str(uuid4()),
            name="Test Tenant",
            slug="test-tenant",
            plan="free",
            is_active=True,
            settings={"key": "value"},
            created_at="2026-09-13T00:00:00+00:00",
            updated_at="2026-09-13T00:00:00+00:00",
        )
        assert resp.name == "Test Tenant"
        assert resp.plan == "free"
        assert resp.is_active is True

    def test_tenant_update_request_partial(self) -> None:
        req = TenantUpdateRequest(name="New Name")
        assert req.name == "New Name"
        assert req.settings is None

    def test_tenant_update_request_with_settings(self) -> None:
        req = TenantUpdateRequest(settings={"feature_x": True})
        assert req.settings == {"feature_x": True}
        assert req.name is None

    def test_invite_member_request_defaults(self) -> None:
        req = InviteMemberRequest(email="user@test.com")
        assert req.role == "member"
        assert req.display_name is None

    def test_invite_member_request_custom_role(self) -> None:
        req = InviteMemberRequest(email="admin@test.com", role="admin")
        assert req.role == "admin"

    def test_invite_member_request_invalid_role(self) -> None:
        with pytest.raises(ValidationError):
            InviteMemberRequest(email="user@test.com", role="invalid_role")

    def test_update_member_role_request(self) -> None:
        req = UpdateMemberRoleRequest(role="viewer")
        assert req.role == "viewer"

    def test_update_member_role_request_invalid(self) -> None:
        with pytest.raises(ValidationError):
            UpdateMemberRoleRequest(role="superadmin")

    def test_tenant_member_response(self) -> None:
        resp = TenantMemberResponse(
            id=str(uuid4()),
            email="user@test.com",
            display_name="Test User",
            role="member",
            is_active=True,
            last_login_at=None,
            created_at="2026-09-13T00:00:00+00:00",
        )
        assert resp.email == "user@test.com"
        assert resp.is_active is True
        assert resp.last_login_at is None


class TestTenantServiceError:
    def test_error_with_default_status(self) -> None:
        err = TenantServiceError("Something went wrong")
        assert err.message == "Something went wrong"
        assert err.status_code == 400

    def test_error_with_custom_status(self) -> None:
        err = TenantServiceError("Not found", status_code=404)
        assert err.status_code == 404
        assert str(err) == "Not found"
