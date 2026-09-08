"""MV5-05 — Trial monitor for 7x24 production deployment availability tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class TrialStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class TrialRecord:
    run_id: str
    started_at: datetime
    status: TrialStatus
    duration_ms: int
    skus_processed: int
    health_status: HealthStatus
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "skus_processed": self.skus_processed,
            "health_status": self.health_status.value,
        }
        if self.error:
            result["error"] = self.error
        return result


class TrialMonitor:
    def __init__(self) -> None:
        self._records: list[TrialRecord] = []

    def add(self, record: TrialRecord) -> None:
        self._records.append(record)

    def get_records(self) -> list[TrialRecord]:
        return list(self._records)

    @property
    def total_runs(self) -> int:
        return len(self._records)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self._records if r.status == TrialStatus.SUCCESS)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self._records if r.status != TrialStatus.SUCCESS)

    @property
    def success_rate(self) -> float:
        if not self._records:
            return 0.0
        return self.success_count / len(self._records)

    @property
    def avg_duration_ms(self) -> float:
        if not self._records:
            return 0.0
        return sum(r.duration_ms for r in self._records) / len(self._records)

    def build_summary(self) -> dict[str, Any]:
        records = self._records
        return {
            "total_runs": len(records),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "availability": compute_availability(records),
            "p95_latency_ms": compute_p95_latency(records),
            "recovery_time_seconds": compute_recovery_time(records),
            "total_skus_processed": sum(r.skus_processed for r in records),
        }


def compute_availability(records: list[TrialRecord]) -> float:
    if not records:
        return 0.0
    successful = sum(1 for r in records if r.status == TrialStatus.SUCCESS)
    return successful / len(records)


def compute_p95_latency(records: list[TrialRecord]) -> int:
    if not records:
        return 0
    durations = sorted(r.duration_ms for r in records)
    idx = int(len(durations) * 0.95)
    idx = min(idx, len(durations) - 1)
    return durations[idx]


def compute_recovery_time(records: list[TrialRecord]) -> float:
    if not records:
        return 0.0

    sorted_records = sorted(records, key=lambda r: r.started_at)

    total_recovery = 0.0
    failure_start: datetime | None = None

    for record in sorted_records:
        if record.status != TrialStatus.SUCCESS:
            if failure_start is None:
                failure_start = record.started_at
        else:
            if failure_start is not None:
                delta = (record.started_at - failure_start).total_seconds()
                total_recovery += delta
                failure_start = None

    if failure_start is not None:
        last_record = sorted_records[-1]
        delta = (last_record.started_at - failure_start).total_seconds()
        total_recovery += delta

    return total_recovery
