"""P5-07/P6-08: Tenant admin schemas and service unit tests."""

import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASEURL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")

import pytest
from aeo_api.auth.quota_service import PlanQuota
from aeo_api.auth.tenant_service import TenantServiceError, invite_member
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


def _make_mock_session(
    tenant_plan: str = "free",
    active_member_count: int = 0,
    existing_email: str | None = None,
) -> AsyncMock:
    session = AsyncMock()

    tenant_mock = MagicMock()
    tenant_mock.plan = tenant_plan

    count_result = MagicMock()
    count_result.scalar_one.return_value = active_member_count

    email_result = MagicMock()
    email_result.scalar_one_or_none.return_value = (
        MagicMock() if existing_email else None
    )

    tenant_result = MagicMock()
    tenant_result.scalar_one_or_none.return_value = tenant_mock

    session.execute = AsyncMock(
        side_effect=[email_result, tenant_result, count_result]
    )
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    return session


class TestInviteMemberQuotaEnforcement:
    @pytest.mark.asyncio
    async def test_invite_under_limit_succeeds(self) -> None:
        session = _make_mock_session(tenant_plan="free", active_member_count=2)
        tenant_id = uuid4()
        mock_quota = PlanQuota(plan="free", monthly_tasks=10, max_users=3, description="Free")

        with patch("aeo_api.auth.tenant_service.get_plan_quota", new=AsyncMock(return_value=mock_quota)):
            user = await invite_member(
                session, tenant_id, email="new@test.com", display_name="New"
            )

        session.add.assert_called_once()
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_invite_at_limit_raises_403(self) -> None:
        session = _make_mock_session(tenant_plan="free", active_member_count=3)
        tenant_id = uuid4()
        mock_quota = PlanQuota(plan="free", monthly_tasks=10, max_users=3, description="Free")

        with patch("aeo_api.auth.tenant_service.get_plan_quota", new=AsyncMock(return_value=mock_quota)):
            with pytest.raises(TenantServiceError) as exc_info:
                await invite_member(
                    session, tenant_id, email="new@test.com"
                )

        assert exc_info.value.status_code == 403
        assert "Member limit reached" in exc_info.value.message
        assert "3/3" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_invite_over_limit_raises_403(self) -> None:
        session = _make_mock_session(tenant_plan="pro", active_member_count=10)
        tenant_id = uuid4()
        mock_quota = PlanQuota(plan="pro", monthly_tasks=100, max_users=10, description="Pro")

        with patch("aeo_api.auth.tenant_service.get_plan_quota", new=AsyncMock(return_value=mock_quota)):
            with pytest.raises(TenantServiceError) as exc_info:
                await invite_member(
                    session, tenant_id, email="new@test.com"
                )

        assert exc_info.value.status_code == 403
        assert "10/10" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_invite_duplicate_email_raises_before_quota_check(self) -> None:
        session = _make_mock_session(
            tenant_plan="free", active_member_count=0, existing_email="dup@test.com"
        )
        tenant_id = uuid4()

        with pytest.raises(TenantServiceError) as exc_info:
            await invite_member(session, tenant_id, email="dup@test.com")

        assert "already exists" in exc_info.value.message
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_invite_enterprise_high_limit(self) -> None:
        session = _make_mock_session(tenant_plan="enterprise", active_member_count=50)
        tenant_id = uuid4()
        mock_quota = PlanQuota(
            plan="enterprise", monthly_tasks=None, max_users=100, description="Enterprise"
        )

        with patch("aeo_api.auth.tenant_service.get_plan_quota", new=AsyncMock(return_value=mock_quota)):
            user = await invite_member(
                session, tenant_id, email="new@test.com"
            )

        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_message_includes_upgrade_hint(self) -> None:
        session = _make_mock_session(tenant_plan="free", active_member_count=3)
        tenant_id = uuid4()
        mock_quota = PlanQuota(plan="free", monthly_tasks=10, max_users=3, description="Free")

        with patch("aeo_api.auth.tenant_service.get_plan_quota", new=AsyncMock(return_value=mock_quota)):
            with pytest.raises(TenantServiceError) as exc_info:
                await invite_member(
                    session, tenant_id, email="new@test.com"
                )

        assert "Upgrade your plan" in exc_info.value.message
