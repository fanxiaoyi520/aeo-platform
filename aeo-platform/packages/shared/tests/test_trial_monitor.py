"""MV5-05: trial monitor — availability and performance tracking for 7x24 trial."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from aeo_shared.trial_monitor import (
    HealthStatus,
    TrialMonitor,
    TrialRecord,
    TrialStatus,
    compute_availability,
    compute_p95_latency,
    compute_recovery_time,
)


def _ok_record(
    *,
    started_at: datetime | None = None,
    duration_ms: int = 200,
    run_id: str = "run-001",
) -> TrialRecord:
    ts = started_at or datetime(2026, 9, 8, 12, 0, 0, tzinfo=UTC)
    return TrialRecord(
        run_id=run_id,
        started_at=ts,
        status=TrialStatus.SUCCESS,
        duration_ms=duration_ms,
        skus_processed=50,
        health_status=HealthStatus.HEALTHY,
    )


def _fail_record(
    *,
    started_at: datetime | None = None,
    duration_ms: int = 5000,
    run_id: str = "run-fail",
    error: str = "timeout",
) -> TrialRecord:
    ts = started_at or datetime(2026, 9, 8, 12, 0, 0, tzinfo=UTC)
    return TrialRecord(
        run_id=run_id,
        started_at=ts,
        status=TrialStatus.FAILED,
        duration_ms=duration_ms,
        skus_processed=0,
        health_status=HealthStatus.DEGRADED,
        error=error,
    )


def test_trial_record_creation() -> None:
    record = _ok_record()
    assert record.run_id == "run-001"
    assert record.status == TrialStatus.SUCCESS
    assert record.health_status == HealthStatus.HEALTHY
    assert record.duration_ms == 200
    assert record.skus_processed == 50


def test_trial_record_to_dict() -> None:
    record = _ok_record()
    d = record.to_dict()
    assert d["run_id"] == "run-001"
    assert d["status"] == "success"
    assert d["health_status"] == "healthy"
    assert d["duration_ms"] == 200


def test_trial_record_failed_with_error() -> None:
    record = _fail_record(error="connection refused")
    assert record.status == TrialStatus.FAILED
    assert record.error == "connection refused"
    d = record.to_dict()
    assert d["error"] == "connection refused"


def test_monitor_empty() -> None:
    monitor = TrialMonitor()
    assert monitor.total_runs == 0
    assert monitor.success_count == 0
    assert monitor.failure_count == 0
    assert monitor.success_rate == 0.0


def test_monitor_add_records() -> None:
    monitor = TrialMonitor()
    monitor.add(_ok_record(run_id="r1"))
    monitor.add(_ok_record(run_id="r2"))
    monitor.add(_fail_record(run_id="r3"))

    assert monitor.total_runs == 3
    assert monitor.success_count == 2
    assert monitor.failure_count == 1


def test_monitor_success_rate() -> None:
    monitor = TrialMonitor()
    for i in range(8):
        monitor.add(_ok_record(run_id=f"ok-{i}"))
    for i in range(2):
        monitor.add(_fail_record(run_id=f"fail-{i}"))

    assert monitor.total_runs == 10
    assert monitor.success_rate == pytest.approx(0.80)


def test_monitor_avg_duration() -> None:
    monitor = TrialMonitor()
    monitor.add(_ok_record(run_id="r1", duration_ms=100))
    monitor.add(_ok_record(run_id="r2", duration_ms=300))
    monitor.add(_fail_record(run_id="r3", duration_ms=5000))

    assert monitor.avg_duration_ms == pytest.approx(1800.0)


def test_compute_availability_all_success() -> None:
    records = [_ok_record(run_id=f"r{i}") for i in range(10)]
    availability = compute_availability(records)
    assert availability == pytest.approx(1.0)


def test_compute_availability_mixed() -> None:
    records = [_ok_record(run_id=f"ok-{i}") for i in range(9)]
    records.append(_fail_record(run_id="fail-0"))
    availability = compute_availability(records)
    assert availability == pytest.approx(0.90)


def test_compute_availability_empty() -> None:
    assert compute_availability([]) == 0.0


def test_compute_p95_latency() -> None:
    records = [_ok_record(run_id=f"r{i}", duration_ms=100 + i * 10) for i in range(20)]
    p95 = compute_p95_latency(records)
    assert p95 >= 280


def test_compute_p95_latency_empty() -> None:
    assert compute_p95_latency([]) == 0


def test_compute_p95_latency_single() -> None:
    records = [_ok_record(duration_ms=150)]
    assert compute_p95_latency(records) == 150


def test_compute_recovery_time_no_failures() -> None:
    records = [_ok_record(run_id=f"r{i}") for i in range(5)]
    assert compute_recovery_time(records) == 0


def test_compute_recovery_time_with_failure() -> None:
    base = datetime(2026, 9, 8, 12, 0, 0, tzinfo=UTC)
    records = [
        _ok_record(run_id="r1", started_at=base, duration_ms=200),
        _fail_record(
            run_id="r2",
            started_at=datetime(2026, 9, 8, 12, 4, 0, tzinfo=UTC),
            duration_ms=5000,
        ),
        _ok_record(
            run_id="r3",
            started_at=datetime(2026, 9, 8, 12, 8, 0, tzinfo=UTC),
            duration_ms=200,
        ),
    ]
    recovery_seconds = compute_recovery_time(records)
    assert recovery_seconds == pytest.approx(240.0)


def test_compute_recovery_time_multiple_failures() -> None:
    base = datetime(2026, 9, 8, 12, 0, 0, tzinfo=UTC)
    records = [
        _ok_record(run_id="r1", started_at=base, duration_ms=200),
        _fail_record(
            run_id="r2",
            started_at=datetime(2026, 9, 8, 12, 4, 0, tzinfo=UTC),
            duration_ms=5000,
        ),
        _fail_record(
            run_id="r3",
            started_at=datetime(2026, 9, 8, 12, 8, 0, tzinfo=UTC),
            duration_ms=5000,
        ),
        _ok_record(
            run_id="r4",
            started_at=datetime(2026, 9, 8, 12, 12, 0, tzinfo=UTC),
            duration_ms=200,
        ),
    ]
    recovery_seconds = compute_recovery_time(records)
    assert recovery_seconds == pytest.approx(480.0)


def test_monitor_build_summary() -> None:
    monitor = TrialMonitor()
    for i in range(10):
        monitor.add(
            _ok_record(
                run_id=f"ok-{i}",
                started_at=datetime(2026, 9, 8, i, 0, 0, tzinfo=UTC),
                duration_ms=200 + i * 10,
            )
        )
    monitor.add(
        _fail_record(
            run_id="fail-0",
            started_at=datetime(2026, 9, 8, 10, 0, 0, tzinfo=UTC),
            duration_ms=5000,
        )
    )

    summary = monitor.build_summary()
    assert summary["total_runs"] == 11
    assert summary["success_count"] == 10
    assert summary["failure_count"] == 1
    assert summary["success_rate"] == pytest.approx(10 / 11)
    assert summary["availability"] == pytest.approx(10 / 11)
    assert summary["p95_latency_ms"] > 0
    assert "recovery_time_seconds" in summary


def test_monitor_build_summary_empty() -> None:
    monitor = TrialMonitor()
    summary = monitor.build_summary()
    assert summary["total_runs"] == 0
    assert summary["availability"] == 0.0
    assert summary["p95_latency_ms"] == 0


def test_monitor_get_records() -> None:
    monitor = TrialMonitor()
    r1 = _ok_record(run_id="r1")
    r2 = _fail_record(run_id="r2")
    monitor.add(r1)
    monitor.add(r2)

    records = monitor.get_records()
    assert len(records) == 2
    assert records[0].run_id == "r1"
    assert records[1].run_id == "r2"


def test_availability_meets_target() -> None:
    records = [_ok_record(run_id=f"r{i}") for i in range(99)]
    records.append(_fail_record(run_id="r-fail"))
    availability = compute_availability(records)
    assert availability >= 0.99


def test_availability_below_target() -> None:
    records = [_ok_record(run_id=f"r{i}") for i in range(98)]
    records.append(_fail_record(run_id="f1"))
    records.append(_fail_record(run_id="f2"))
    availability = compute_availability(records)
    assert availability < 0.99
