"""P7-24: Tenant-level monitoring and billing reconciliation.

Records per-tenant operational events (API calls, errors, latency)
and reconciles Stripe invoices against actual usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class EventKind(StrEnum):
    API_CALL = "api_call"
    ERROR = "error"
    LATENCY = "latency_ms"


@dataclass(frozen=True)
class TenantEvent:
    """One operational event for a tenant."""

    tenant_id: str
    kind: EventKind
    value: float
    endpoint: str = ""
    timestamp: float = 0.0


@dataclass(frozen=True)
class TenantMetrics:
    """Aggregated metrics for one tenant over a window."""

    tenant_id: str
    api_calls: int = 0
    errors: int = 0
    latency_sum_ms: float = 0.0
    latency_count: int = 0

    @property
    def average_latency_ms(self) -> float:
        if self.latency_count == 0:
            return 0.0
        return self.latency_sum_ms / self.latency_count

    @property
    def error_rate(self) -> float:
        if self.api_calls == 0:
            return 0.0
        return self.errors / self.api_calls


@dataclass(frozen=True)
class ReconciliationFinding:
    """One discrepancy between billed and actual usage."""

    tenant_id: str
    billed_api_calls: int
    actual_api_calls: int
    delta: int
    ok: bool


@dataclass(frozen=True)
class ReconciliationReport:
    """Full reconciliation result across tenants."""

    findings: list[ReconciliationFinding]
    total_billed: int
    total_actual: int

    @property
    def total_delta(self) -> int:
        return self.total_actual - self.total_billed

    @property
    def is_balanced(self) -> bool:
        return self.total_delta == 0


class MetricsStore(Protocol):
    """Persistence interface for tenant metrics."""

    def get_metrics(self, tenant_id: str) -> TenantMetrics: ...
    def save_metrics(self, metrics: TenantMetrics) -> None: ...


@dataclass
class InMemoryMetricsStore:
    """Simple in-memory store for tests and single-process deployments."""

    _metrics: dict[str, TenantMetrics] = field(default_factory=dict)

    def get_metrics(self, tenant_id: str) -> TenantMetrics:
        return self._metrics.get(
            tenant_id, TenantMetrics(tenant_id=tenant_id)
        )

    def save_metrics(self, metrics: TenantMetrics) -> None:
        self._metrics[metrics.tenant_id] = metrics

    def reset(self) -> None:
        self._metrics.clear()


@dataclass
class TenantMonitoringService:
    """Records events and aggregates per-tenant metrics."""

    store: MetricsStore

    def record(self, event: TenantEvent) -> TenantMetrics:
        metrics = self.store.get_metrics(event.tenant_id)
        if event.kind == EventKind.API_CALL:
            metrics = TenantMetrics(
                tenant_id=metrics.tenant_id,
                api_calls=metrics.api_calls + 1,
                errors=metrics.errors,
                latency_sum_ms=metrics.latency_sum_ms,
                latency_count=metrics.latency_count,
            )
        elif event.kind == EventKind.ERROR:
            metrics = TenantMetrics(
                tenant_id=metrics.tenant_id,
                api_calls=metrics.api_calls,
                errors=metrics.errors + 1,
                latency_sum_ms=metrics.latency_sum_ms,
                latency_count=metrics.latency_count,
            )
        elif event.kind == EventKind.LATENCY:
            metrics = TenantMetrics(
                tenant_id=metrics.tenant_id,
                api_calls=metrics.api_calls,
                errors=metrics.errors,
                latency_sum_ms=metrics.latency_sum_ms + event.value,
                latency_count=metrics.latency_count + 1,
            )
        self.store.save_metrics(metrics)
        return metrics

    def get_metrics(self, tenant_id: str) -> TenantMetrics:
        return self.store.get_metrics(tenant_id)


@dataclass
class BillingReconciler:
    """Compares Stripe invoices against actual usage."""

    monitoring: TenantMonitoringService

    def reconcile(
        self,
        billed_usage: dict[str, int],
    ) -> ReconciliationReport:
        """Compare billed API-call counts against actuals.

        ``billed_usage`` maps ``tenant_id`` → ``api_calls_billed``.
        Tenants present in actuals but absent from billing are treated
        as 0 billed.
        """
        findings: list[ReconciliationFinding] = []
        total_billed = 0
        total_actual = 0
        for tenant_id, billed in billed_usage.items():
            actual = self.monitoring.get_metrics(tenant_id).api_calls
            findings.append(
                ReconciliationFinding(
                    tenant_id=tenant_id,
                    billed_api_calls=billed,
                    actual_api_calls=actual,
                    delta=actual - billed,
                    ok=actual == billed,
                )
            )
            total_billed += billed
            total_actual += actual
        return ReconciliationReport(
            findings=findings,
            total_billed=total_billed,
            total_actual=total_actual,
        )
