"""MV2-03 — cron scheduler tests (RED phase)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from aeo_shared.cron_scheduler import (
    CronScheduler,
    CronSchedulerConfig,
)


class TestCronJobRegistration:
    def test_register_job(self) -> None:
        scheduler = CronScheduler()
        job = scheduler.register(
            job_id="scan-sku1",
            cron_expression="0 9 * * *",
            payload={"sku": "SKU1"},
        )
        assert job.job_id == "scan-sku1"
        assert job.cron_expression == "0 9 * * *"
        assert job.payload == {"sku": "SKU1"}
        assert job.enabled is True

    def test_register_job_invalid_cron(self) -> None:
        scheduler = CronScheduler()
        with pytest.raises(ValueError, match="expected 5 fields"):
            scheduler.register(job_id="bad", cron_expression="invalid")

    def test_register_duplicate_job_id(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        with pytest.raises(ValueError, match="already registered"):
            scheduler.register(job_id="j1", cron_expression="0 10 * * *")

    def test_list_jobs(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        scheduler.register(job_id="j2", cron_expression="0 10 * * *")
        jobs = scheduler.list_jobs()
        assert len(jobs) == 2
        ids = {j.job_id for j in jobs}
        assert ids == {"j1", "j2"}

    def test_get_job(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        job = scheduler.get("j1")
        assert job.job_id == "j1"

    def test_get_nonexistent_job(self) -> None:
        scheduler = CronScheduler()
        with pytest.raises(KeyError):
            scheduler.get("nonexistent")

    def test_delete_job(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        scheduler.delete("j1")
        assert len(scheduler.list_jobs()) == 0

    def test_delete_nonexistent_job(self) -> None:
        scheduler = CronScheduler()
        with pytest.raises(KeyError):
            scheduler.delete("nonexistent")


class TestCronSchedulerTick:
    def test_tick_returns_due_job(self) -> None:
        scheduler = CronScheduler()
        ref = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
        scheduler.register(job_id="j1", cron_expression="0 9 * * *", now=ref)
        now = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        due = scheduler.tick(now)
        assert len(due) == 1
        assert due[0].job_id == "j1"

    def test_tick_skips_not_due_job(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        now = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
        due = scheduler.tick(now)
        assert due == []

    def test_tick_multiple_due_jobs(self) -> None:
        scheduler = CronScheduler()
        ref = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
        scheduler.register(job_id="j1", cron_expression="0 9 * * *", now=ref)
        scheduler.register(job_id="j2", cron_expression="0 9 * * *", now=ref)
        now = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        due = scheduler.tick(now)
        assert len(due) == 2

    def test_tick_disabled_job_not_returned(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        scheduler.disable("j1")
        now = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        due = scheduler.tick(now)
        assert due == []

    def test_tick_updates_last_run(self) -> None:
        scheduler = CronScheduler()
        ref = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
        scheduler.register(job_id="j1", cron_expression="0 9 * * *", now=ref)
        now = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        scheduler.tick(now)
        job = scheduler.get("j1")
        assert job.last_run_at == now

    def test_tick_does_not_double_trigger(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        now = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        scheduler.tick(now)
        second_tick = scheduler.tick(now)
        assert second_tick == []

    def test_tick_fires_again_next_period(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        day1 = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        scheduler.tick(day1)
        day2 = datetime(2026, 9, 5, 9, 0, tzinfo=UTC)
        due = scheduler.tick(day2)
        assert len(due) == 1

    def test_tick_naive_datetime_treated_as_utc(self) -> None:
        scheduler = CronScheduler()
        ref = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
        scheduler.register(job_id="j1", cron_expression="0 9 * * *", now=ref)
        now = datetime(2026, 9, 4, 9, 0)
        due = scheduler.tick(now)
        assert len(due) == 1


class TestCronSchedulerEnableDisable:
    def test_disable_job(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        scheduler.disable("j1")
        job = scheduler.get("j1")
        assert job.enabled is False

    def test_enable_job(self) -> None:
        scheduler = CronScheduler()
        scheduler.register(job_id="j1", cron_expression="0 9 * * *")
        scheduler.disable("j1")
        scheduler.enable("j1")
        job = scheduler.get("j1")
        assert job.enabled is True

    def test_disable_nonexistent(self) -> None:
        scheduler = CronScheduler()
        with pytest.raises(KeyError):
            scheduler.disable("nonexistent")

    def test_enable_nonexistent(self) -> None:
        scheduler = CronScheduler()
        with pytest.raises(KeyError):
            scheduler.enable("nonexistent")


class TestCronSchedulerConfig:
    def test_default_config(self) -> None:
        config = CronSchedulerConfig()
        assert config.max_jobs_per_tick == 10

    def test_scheduler_with_config(self) -> None:
        config = CronSchedulerConfig(max_jobs_per_tick=1)
        scheduler = CronScheduler(config=config)
        ref = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
        scheduler.register(job_id="j1", cron_expression="0 9 * * *", now=ref)
        scheduler.register(job_id="j2", cron_expression="0 9 * * *", now=ref)
        now = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)
        due = scheduler.tick(now)
        assert len(due) == 1
