"""MV2-03 — cron-based job scheduler (pure logic, no framework).

Registers jobs with cron expressions and determines which are due on each
``tick(now)`` call.  Does not run an event loop — the caller (API worker,
background task) is responsible for invoking ``tick`` periodically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from aeo_shared.cron_parser import CronSchedule, next_run, parse_cron


class CronSchedulerConfig(BaseModel):
    """Tuning knobs for the cron scheduler."""

    max_jobs_per_tick: int = 10


@dataclass
class CronJob:
    """A registered cron job with schedule tracking."""

    job_id: str
    cron_expression: str
    schedule: CronSchedule
    payload: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None


class CronScheduler:
    """In-memory cron scheduler — register jobs and poll with ``tick``."""

    def __init__(self, config: CronSchedulerConfig | None = None) -> None:
        self._config = config or CronSchedulerConfig()
        self._jobs: dict[str, CronJob] = {}

    @property
    def config(self) -> CronSchedulerConfig:
        return self._config

    def register(
        self,
        *,
        job_id: str,
        cron_expression: str,
        payload: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> CronJob:
        if job_id in self._jobs:
            msg = f"Job already registered: {job_id}"
            raise ValueError(msg)
        schedule = parse_cron(cron_expression)
        ref = now or datetime.now(UTC)
        job = CronJob(
            job_id=job_id,
            cron_expression=cron_expression,
            schedule=schedule,
            payload=payload or {},
            next_run_at=next_run(schedule, ref),
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> CronJob:
        try:
            return self._jobs[job_id]
        except KeyError:
            msg = f"Job not found: {job_id}"
            raise KeyError(msg) from None

    def list_jobs(self) -> list[CronJob]:
        return list(self._jobs.values())

    def delete(self, job_id: str) -> None:
        if job_id not in self._jobs:
            msg = f"Job not found: {job_id}"
            raise KeyError(msg) from None
        del self._jobs[job_id]

    def enable(self, job_id: str) -> None:
        job = self.get(job_id)
        job.enabled = True

    def disable(self, job_id: str) -> None:
        job = self.get(job_id)
        job.enabled = False

    def tick(self, now: datetime) -> list[CronJob]:
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        due: list[CronJob] = []
        for job in self._jobs.values():
            if not job.enabled:
                continue
            if job.next_run_at is not None and now < job.next_run_at:
                continue
            if job.next_run_at is not None and now >= job.next_run_at:
                job.last_run_at = now
                job.next_run_at = next_run(job.schedule, now)
                due.append(job)
                if len(due) >= self._config.max_jobs_per_tick:
                    break
        return due
