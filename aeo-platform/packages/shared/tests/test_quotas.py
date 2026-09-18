"""P7-23: Tests for resource quota management."""

from __future__ import annotations

import pytest
from aeo_shared.quotas import (
    PLAN_LIMITS,
    InMemoryQuotaStore,
    PlanTier,
    QuotaExceededError,
    QuotaKind,
    QuotaLimits,
    QuotaService,
    QuotaUsage,
)


class TestPlanLimits:
    def test_all_plan_tiers_have_limits(self) -> None:
        for tier in PlanTier:
            limits = PLAN_LIMITS[tier]
            assert isinstance(limits, QuotaLimits)
            assert limits.api_calls_per_day > 0
            assert limits.storage_bytes > 0
            assert limits.concurrent_jobs > 0

    def test_higher_tiers_have_higher_limits(self) -> None:
        free = PLAN_LIMITS[PlanTier.FREE]
        starter = PLAN_LIMITS[PlanTier.STARTER]
        pro = PLAN_LIMITS[PlanTier.PRO]
        enterprise = PLAN_LIMITS[PlanTier.ENTERPRISE]
        assert free.api_calls_per_day < starter.api_calls_per_day
        assert starter.api_calls_per_day < pro.api_calls_per_day
        assert pro.api_calls_per_day < enterprise.api_calls_per_day


class TestQuotaService:
    def test_default_usage_is_zero(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        usage = service.get_usage("tenant-1")
        assert usage.api_calls == 0
        assert usage.storage_bytes == 0
        assert usage.concurrent_jobs == 0

    def test_consume_api_calls(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        new_usage = service.consume("tenant-1", QuotaKind.API_CALLS, 5)
        assert new_usage.api_calls == 5
        assert service.get_usage("tenant-1").api_calls == 5

    def test_consume_storage_bytes(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        new_usage = service.consume(
            "tenant-1", QuotaKind.STORAGE_BYTES, 1000
        )
        assert new_usage.storage_bytes == 1000

    def test_consume_concurrent_jobs(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        new_usage = service.consume(
            "tenant-1", QuotaKind.CONCURRENT_JOBS, 1
        )
        assert new_usage.concurrent_jobs == 1

    def test_consume_raises_when_exceeded(self) -> None:
        store = InMemoryQuotaStore()
        service = QuotaService(store=store, plan_tier=PlanTier.FREE)
        # FREE tier: 100 API calls/day
        service.consume("tenant-1", QuotaKind.API_CALLS, 99)
        with pytest.raises(QuotaExceededError) as exc_info:
            service.consume("tenant-1", QuotaKind.API_CALLS, 5)
        assert exc_info.value.kind == QuotaKind.API_CALLS
        assert exc_info.value.limit == 100
        assert exc_info.value.used == 99

    def test_check_returns_true_when_within_limit(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        assert service.check("tenant-1", QuotaKind.API_CALLS, 1) is True

    def test_check_returns_false_when_would_exceed(self) -> None:
        store = InMemoryQuotaStore()
        service = QuotaService(store=store, plan_tier=PlanTier.FREE)
        service.consume("tenant-1", QuotaKind.API_CALLS, 100)
        assert service.check("tenant-1", QuotaKind.API_CALLS, 1) is False

    def test_release_decrements_concurrent_jobs(self) -> None:
        service = QuotaService(
            store=InMemoryQuotaStore(), plan_tier=PlanTier.PRO
        )
        service.consume("tenant-1", QuotaKind.CONCURRENT_JOBS, 2)
        new_usage = service.release("tenant-1", QuotaKind.CONCURRENT_JOBS, 1)
        assert new_usage.concurrent_jobs == 1

    def test_release_does_not_go_negative(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        new_usage = service.release("tenant-1", QuotaKind.CONCURRENT_JOBS, 5)
        assert new_usage.concurrent_jobs == 0

    def test_different_kinds_are_independent(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        service.consume("tenant-1", QuotaKind.API_CALLS, 10)
        service.consume("tenant-1", QuotaKind.STORAGE_BYTES, 500)
        usage = service.get_usage("tenant-1")
        assert usage.api_calls == 10
        assert usage.storage_bytes == 500
        assert usage.concurrent_jobs == 0

    def test_multiple_tenants_are_isolated(self) -> None:
        service = QuotaService(store=InMemoryQuotaStore())
        service.consume("tenant-A", QuotaKind.API_CALLS, 10)
        service.consume("tenant-B", QuotaKind.API_CALLS, 5)
        assert service.get_usage("tenant-A").api_calls == 10
        assert service.get_usage("tenant-B").api_calls == 5

    def test_plan_tier_changes_limits(self) -> None:
        store = InMemoryQuotaStore()
        free = QuotaService(store=store, plan_tier=PlanTier.FREE)
        free.consume("tenant-1", QuotaKind.API_CALLS, 99)
        # Upgrade to PRO
        pro = QuotaService(store=store, plan_tier=PlanTier.PRO)
        # PRO limit is 10,000 → can consume more
        pro.consume("tenant-1", QuotaKind.API_CALLS, 100)
        assert pro.get_usage("tenant-1").api_calls == 199


class TestQuotaExceededError:
    def test_error_message(self) -> None:
        err = QuotaExceededError(QuotaKind.API_CALLS, 100, 99)
        assert "api_calls" in str(err)
        assert "99" in str(err)
        assert "100" in str(err)


class TestQuotaUsage:
    def test_is_dataclass(self) -> None:
        usage = QuotaUsage(tenant_id="t1")
        assert usage.tenant_id == "t1"
        assert usage.api_calls == 0
