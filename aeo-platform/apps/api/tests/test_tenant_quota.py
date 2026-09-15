"""P5-08: Tenant quota service unit tests."""

import os
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASEURL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")

import pytest
from aeo_api.auth.quota_service import (
    FALLBACK_QUOTAS,
    PlanQuota,
    check_task_quota,
    get_plan_quota,
    get_task_usage,
    increment_task_usage,
)


class TestPlanQuotas:
    @pytest.mark.asyncio
    async def test_free_plan_quota(self) -> None:
        quota = await get_plan_quota(None, "free")
        assert quota.plan == "free"
        assert quota.monthly_tasks == 10
        assert quota.max_users == 3

    @pytest.mark.asyncio
    async def test_pro_plan_quota(self) -> None:
        quota = await get_plan_quota(None, "pro")
        assert quota.plan == "pro"
        assert quota.monthly_tasks == 100
        assert quota.max_users == 10

    @pytest.mark.asyncio
    async def test_enterprise_plan_quota(self) -> None:
        quota = await get_plan_quota(None, "enterprise")
        assert quota.plan == "enterprise"
        assert quota.monthly_tasks is None
        assert quota.max_users == 100

    @pytest.mark.asyncio
    async def test_unknown_plan_defaults_to_free(self) -> None:
        quota = await get_plan_quota(None, "unknown_plan")
        assert quota.plan == "free"
        assert quota.monthly_tasks == 10

    def test_all_plans_defined(self) -> None:
        assert "free" in FALLBACK_QUOTAS
        assert "pro" in FALLBACK_QUOTAS
        assert "enterprise" in FALLBACK_QUOTAS


class TestPlanQuotaDataclass:
    def test_plan_quota_frozen(self) -> None:
        quota = PlanQuota(plan="test", monthly_tasks=50, max_users=5, description="Test")
        with pytest.raises(AttributeError):
            quota.plan = "changed"  # type: ignore[misc]

    def test_plan_quota_fields(self) -> None:
        quota = PlanQuota(plan="test", monthly_tasks=50, max_users=5, description="Test plan")
        assert quota.plan == "test"
        assert quota.monthly_tasks == 50
        assert quota.max_users == 5
        assert quota.description == "Test plan"


class TestCheckTaskQuota:
    @pytest.mark.asyncio
    async def test_enterprise_always_allowed(self) -> None:
        with patch("aeo_api.auth.quota_service.get_task_usage", return_value=9999):
            allowed, used, limit = await check_task_quota("tenant-1", "enterprise", None)
            assert allowed is True
            assert used == 9999
            assert limit is None

    @pytest.mark.asyncio
    async def test_free_under_limit(self) -> None:
        with patch("aeo_api.auth.quota_service.get_task_usage", return_value=5):
            allowed, used, limit = await check_task_quota("tenant-1", "free", None)
            assert allowed is True
            assert used == 5
            assert limit == 10

    @pytest.mark.asyncio
    async def test_free_at_limit(self) -> None:
        with patch("aeo_api.auth.quota_service.get_task_usage", return_value=10):
            allowed, used, limit = await check_task_quota("tenant-1", "free", None)
            assert allowed is False
            assert used == 10
            assert limit == 10

    @pytest.mark.asyncio
    async def test_free_over_limit(self) -> None:
        with patch("aeo_api.auth.quota_service.get_task_usage", return_value=15):
            allowed, used, limit = await check_task_quota("tenant-1", "free", None)
            assert allowed is False
            assert used == 15
            assert limit == 10

    @pytest.mark.asyncio
    async def test_pro_under_limit(self) -> None:
        with patch("aeo_api.auth.quota_service.get_task_usage", return_value=50):
            allowed, used, limit = await check_task_quota("tenant-1", "pro", None)
            assert allowed is True
            assert used == 50
            assert limit == 100


class TestGetTaskUsage:
    @pytest.mark.asyncio
    async def test_usage_returns_zero_when_no_key(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        with patch("aeo_api.auth.quota_service.get_redis", return_value=mock_redis):
            usage = await get_task_usage("tenant-1")
            assert usage == 0

    @pytest.mark.asyncio
    async def test_usage_returns_count(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="42")
        with patch("aeo_api.auth.quota_service.get_redis", return_value=mock_redis):
            usage = await get_task_usage("tenant-1")
            assert usage == 42


class TestIncrementTaskUsage:
    @pytest.mark.asyncio
    async def test_increment_returns_count(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=5)
        mock_redis.expire = AsyncMock()
        with patch("aeo_api.auth.quota_service.get_redis", return_value=mock_redis):
            count = await increment_task_usage("tenant-1")
            assert count == 5

    @pytest.mark.asyncio
    async def test_increment_sets_expiry_on_first(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        with patch("aeo_api.auth.quota_service.get_redis", return_value=mock_redis):
            await increment_task_usage("tenant-1")
            mock_redis.expire.assert_called_once()
