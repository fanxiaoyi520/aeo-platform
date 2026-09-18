"""P7-24: Tests for tenant monitoring and billing reconciliation."""

from __future__ import annotations

from aeo_shared.tenant_monitoring import (
    BillingReconciler,
    EventKind,
    InMemoryMetricsStore,
    ReconciliationFinding,
    ReconciliationReport,
    TenantEvent,
    TenantMetrics,
    TenantMonitoringService,
)


class TestTenantMetrics:
    def test_average_latency_zero_when_no_samples(self) -> None:
        metrics = TenantMetrics(tenant_id="t1")
        assert metrics.average_latency_ms == 0.0

    def test_average_latency_calculation(self) -> None:
        metrics = TenantMetrics(
            tenant_id="t1", latency_sum_ms=300.0, latency_count=3
        )
        assert metrics.average_latency_ms == 100.0

    def test_error_rate_zero_when_no_calls(self) -> None:
        metrics = TenantMetrics(tenant_id="t1")
        assert metrics.error_rate == 0.0

    def test_error_rate_calculation(self) -> None:
        metrics = TenantMetrics(
            tenant_id="t1", api_calls=100, errors=5
        )
        assert metrics.error_rate == 0.05


class TestTenantMonitoringService:
    def test_record_api_call(self) -> None:
        service = TenantMonitoringService(store=InMemoryMetricsStore())
        event = TenantEvent(
            tenant_id="t1", kind=EventKind.API_CALL, value=1
        )
        metrics = service.record(event)
        assert metrics.api_calls == 1
        assert metrics.errors == 0

    def test_record_error(self) -> None:
        service = TenantMonitoringService(store=InMemoryMetricsStore())
        service.record(
            TenantEvent(
                tenant_id="t1", kind=EventKind.API_CALL, value=1
            )
        )
        service.record(
            TenantEvent(tenant_id="t1", kind=EventKind.ERROR, value=1)
        )
        metrics = service.get_metrics("t1")
        assert metrics.api_calls == 1
        assert metrics.errors == 1
        assert metrics.error_rate == 1.0

    def test_record_latency(self) -> None:
        service = TenantMonitoringService(store=InMemoryMetricsStore())
        service.record(
            TenantEvent(
                tenant_id="t1", kind=EventKind.LATENCY, value=150.0
            )
        )
        service.record(
            TenantEvent(
                tenant_id="t1", kind=EventKind.LATENCY, value=250.0
            )
        )
        metrics = service.get_metrics("t1")
        assert metrics.latency_count == 2
        assert metrics.average_latency_ms == 200.0

    def test_unknown_tenant_returns_zero_metrics(self) -> None:
        service = TenantMonitoringService(store=InMemoryMetricsStore())
        metrics = service.get_metrics("unknown")
        assert metrics.api_calls == 0
        assert metrics.errors == 0

    def test_multiple_tenants_isolated(self) -> None:
        service = TenantMonitoringService(store=InMemoryMetricsStore())
        service.record(
            TenantEvent(
                tenant_id="t-A", kind=EventKind.API_CALL, value=1
            )
        )
        service.record(
            TenantEvent(
                tenant_id="t-B", kind=EventKind.API_CALL, value=1
            )
        )
        service.record(
            TenantEvent(
                tenant_id="t-B", kind=EventKind.API_CALL, value=1
            )
        )
        assert service.get_metrics("t-A").api_calls == 1
        assert service.get_metrics("t-B").api_calls == 2


class TestBillingReconciler:
    def test_balanced_reconciliation(self) -> None:
        monitoring = TenantMonitoringService(
            store=InMemoryMetricsStore()
        )
        for _ in range(100):
            monitoring.record(
                TenantEvent(
                    tenant_id="t1", kind=EventKind.API_CALL, value=1
                )
            )
        reconciler = BillingReconciler(monitoring=monitoring)
        report = reconciler.reconcile({"t1": 100})
        assert report.is_balanced is True
        assert report.total_delta == 0
        assert report.findings[0].ok is True

    def test_under_billed_detected(self) -> None:
        monitoring = TenantMonitoringService(
            store=InMemoryMetricsStore()
        )
        for _ in range(150):
            monitoring.record(
                TenantEvent(
                    tenant_id="t1", kind=EventKind.API_CALL, value=1
                )
            )
        reconciler = BillingReconciler(monitoring=monitoring)
        report = reconciler.reconcile({"t1": 100})
        assert report.is_balanced is False
        assert report.total_delta == 50
        finding = report.findings[0]
        assert finding.ok is False
        assert finding.delta == 50

    def test_over_billed_detected(self) -> None:
        monitoring = TenantMonitoringService(
            store=InMemoryMetricsStore()
        )
        for _ in range(50):
            monitoring.record(
                TenantEvent(
                    tenant_id="t1", kind=EventKind.API_CALL, value=1
                )
            )
        reconciler = BillingReconciler(monitoring=monitoring)
        report = reconciler.reconcile({"t1": 100})
        assert report.total_delta == -50

    def test_multiple_tenants_in_report(self) -> None:
        monitoring = TenantMonitoringService(
            store=InMemoryMetricsStore()
        )
        for _ in range(10):
            monitoring.record(
                TenantEvent(
                    tenant_id="t-A", kind=EventKind.API_CALL, value=1
                )
            )
        for _ in range(20):
            monitoring.record(
                TenantEvent(
                    tenant_id="t-B", kind=EventKind.API_CALL, value=1
                )
            )
        reconciler = BillingReconciler(monitoring=monitoring)
        report = reconciler.reconcile({"t-A": 10, "t-B": 20})
        assert len(report.findings) == 2
        assert report.total_billed == 30
        assert report.total_actual == 30
        assert report.is_balanced is True


class TestReconciliationReport:
    def test_is_dataclass(self) -> None:
        report = ReconciliationReport(
            findings=[], total_billed=0, total_actual=0
        )
        assert report.is_balanced is True
        assert report.total_delta == 0


class TestReconciliationFinding:
    def test_is_dataclass(self) -> None:
        finding = ReconciliationFinding(
            tenant_id="t1",
            billed_api_calls=100,
            actual_api_calls=100,
            delta=0,
            ok=True,
        )
        assert finding.ok is True
