"""P7-23: Resource quota management.

Tracks per-tenant usage of rate-limited resources (API calls, storage,
concurrent jobs) and rejects operations that would exceed the plan's
limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class QuotaKind(StrEnum):
    API_CALLS = "api_calls"
    STORAGE_BYTES = "storage_bytes"
    CONCURRENT_JOBS = "concurrent_jobs"


class PlanTier(StrEnum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class QuotaLimits:
    """Per-plan limits."""

    api_calls_per_day: int
    storage_bytes: int
    concurrent_jobs: int


PLAN_LIMITS: dict[PlanTier, QuotaLimits] = {
    PlanTier.FREE: QuotaLimits(
        api_calls_per_day=100,
        storage_bytes=100_000_000,
        concurrent_jobs=1,
    ),
    PlanTier.STARTER: QuotaLimits(
        api_calls_per_day=1_000,
        storage_bytes=1_000_000_000,
        concurrent_jobs=3,
    ),
    PlanTier.PRO: QuotaLimits(
        api_calls_per_day=10_000,
        storage_bytes=10_000_000_000,
        concurrent_jobs=10,
    ),
    PlanTier.ENTERPRISE: QuotaLimits(
        api_calls_per_day=100_000,
        storage_bytes=100_000_000_000,
        concurrent_jobs=50,
    ),
}


@dataclass(frozen=True)
class QuotaUsage:
    """Current usage for one tenant."""

    tenant_id: str
    api_calls: int = 0
    storage_bytes: int = 0
    concurrent_jobs: int = 0


class QuotaExceededError(Exception):
    """Raised when a consume() would exceed the plan limit."""

    def __init__(self, kind: QuotaKind, limit: int, used: int) -> None:
        self.kind = kind
        self.limit = limit
        self.used = used
        super().__init__(
            f"Quota exceeded: {kind.value} ({used}/{limit})"
        )


class QuotaStore(Protocol):
    """Persistence interface for usage counters."""

    def get_usage(self, tenant_id: str) -> QuotaUsage: ...
    def save_usage(self, usage: QuotaUsage) -> None: ...


@dataclass
class InMemoryQuotaStore:
    """Simple in-memory store for tests and single-process deployments."""

    _usage: dict[str, QuotaUsage] = field(default_factory=dict)

    def get_usage(self, tenant_id: str) -> QuotaUsage:
        return self._usage.get(
            tenant_id, QuotaUsage(tenant_id=tenant_id)
        )

    def save_usage(self, usage: QuotaUsage) -> None:
        self._usage[usage.tenant_id] = usage

    def reset(self) -> None:
        self._usage.clear()


@dataclass
class QuotaService:
    """Enforces plan limits against a QuotaStore."""

    store: QuotaStore
    plan_tier: PlanTier = PlanTier.FREE

    @property
    def limits(self) -> QuotaLimits:
        return PLAN_LIMITS[self.plan_tier]

    def get_usage(self, tenant_id: str) -> QuotaUsage:
        return self.store.get_usage(tenant_id)

    def check(
        self, tenant_id: str, kind: QuotaKind, amount: int = 1
    ) -> bool:
        usage = self.get_usage(tenant_id)
        limit = self._limit_for(kind)
        used = self._used_for(usage, kind)
        return used + amount <= limit

    def consume(
        self, tenant_id: str, kind: QuotaKind, amount: int = 1
    ) -> QuotaUsage:
        usage = self.get_usage(tenant_id)
        limit = self._limit_for(kind)
        used = self._used_for(usage, kind)
        if used + amount > limit:
            raise QuotaExceededError(kind, limit, used)
        new_usage = QuotaUsage(
            tenant_id=tenant_id,
            api_calls=usage.api_calls
            + (amount if kind == QuotaKind.API_CALLS else 0),
            storage_bytes=usage.storage_bytes
            + (amount if kind == QuotaKind.STORAGE_BYTES else 0),
            concurrent_jobs=usage.concurrent_jobs
            + (amount if kind == QuotaKind.CONCURRENT_JOBS else 0),
        )
        self.store.save_usage(new_usage)
        return new_usage

    def release(
        self, tenant_id: str, kind: QuotaKind, amount: int = 1
    ) -> QuotaUsage:
        """Release a held resource (concurrency only, typically)."""
        usage = self.get_usage(tenant_id)
        new_value = max(0, self._used_for(usage, kind) - amount)
        new_usage = QuotaUsage(
            tenant_id=tenant_id,
            api_calls=usage.api_calls
            if kind != QuotaKind.API_CALLS
            else max(0, usage.api_calls - amount),
            storage_bytes=usage.storage_bytes
            if kind != QuotaKind.STORAGE_BYTES
            else max(0, usage.storage_bytes - amount),
            concurrent_jobs=usage.concurrent_jobs
            if kind != QuotaKind.CONCURRENT_JOBS
            else new_value,
        )
        self.store.save_usage(new_usage)
        return new_usage

    def _limit_for(self, kind: QuotaKind) -> int:
        limits = self.limits
        return {
            QuotaKind.API_CALLS: limits.api_calls_per_day,
            QuotaKind.STORAGE_BYTES: limits.storage_bytes,
            QuotaKind.CONCURRENT_JOBS: limits.concurrent_jobs,
        }[kind]

    @staticmethod
    def _used_for(usage: QuotaUsage, kind: QuotaKind) -> int:
        return {
            QuotaKind.API_CALLS: usage.api_calls,
            QuotaKind.STORAGE_BYTES: usage.storage_bytes,
            QuotaKind.CONCURRENT_JOBS: usage.concurrent_jobs,
        }[kind]
