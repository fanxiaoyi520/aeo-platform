#!/usr/bin/env python3
"""MV5-05 — 7x24 trial run script for production deployment validation.

Runs periodic batch pilots and health checks, recording availability metrics.
Supports --dry-run mode for testing without Docker/production environment.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aeo_shared.trial_monitor import (
    HealthStatus,
    TrialMonitor,
    TrialRecord,
    TrialStatus,
    compute_availability,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"
DEFAULT_INTERVAL_HOURS = 4
DEFAULT_DURATION_HOURS = 168  # 7 days


def _default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"mv5-trial-{stamp}.json"


def check_health(api_url: str = "http://localhost:8000") -> dict[str, Any]:
    try:
        import urllib.request

        req = urllib.request.Request(f"{api_url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"healthy": data.get("status") == "ok", "data": data}
    except Exception as exc:
        return {"healthy": False, "error": str(exc)}


def simulate_trial_run(
    run_id: str,
    *,
    dry_run: bool = False,
) -> TrialRecord:
    started_at = datetime.now(UTC)

    if dry_run:
        return TrialRecord(
            run_id=run_id,
            started_at=started_at,
            status=TrialStatus.SUCCESS,
            duration_ms=200,
            skus_processed=50,
            health_status=HealthStatus.HEALTHY,
        )

    health = check_health()
    if not health["healthy"]:
        return TrialRecord(
            run_id=run_id,
            started_at=started_at,
            status=TrialStatus.FAILED,
            duration_ms=0,
            skus_processed=0,
            health_status=HealthStatus.DOWN,
            error=health.get("error", "health check failed"),
        )

    started = time.perf_counter()
    try:
        from scripts.batch_mv5_pilot import load_testset, run_batch, ALL_AGENTS

        testset_path = ROOT / "pilot" / "mv5-50sku-testset.json"
        items = load_testset(testset_path)

        import asyncio

        results = asyncio.run(run_batch(items, agents=ALL_AGENTS))

        duration_ms = int((time.perf_counter() - started) * 1000)
        total_agents = sum(len(r.agents) for r in results)
        completed = sum(
            1 for r in results for a in r.agents if a.status == "completed"
        )

        if completed / total_agents >= 0.9 if total_agents > 0 else False:
            return TrialRecord(
                run_id=run_id,
                started_at=started_at,
                status=TrialStatus.SUCCESS,
                duration_ms=duration_ms,
                skus_processed=len(results),
                health_status=HealthStatus.HEALTHY,
            )
        else:
            return TrialRecord(
                run_id=run_id,
                started_at=started_at,
                status=TrialStatus.FAILED,
                duration_ms=duration_ms,
                skus_processed=len(results),
                health_status=HealthStatus.DEGRADED,
                error=f"low success rate: {completed}/{total_agents}",
            )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return TrialRecord(
            run_id=run_id,
            started_at=started_at,
            status=TrialStatus.FAILED,
            duration_ms=duration_ms,
            skus_processed=0,
            health_status=HealthStatus.DEGRADED,
            error=str(exc),
        )


def run_trial(
    *,
    interval_hours: int = DEFAULT_INTERVAL_HOURS,
    duration_hours: int = DEFAULT_DURATION_HOURS,
    dry_run: bool = False,
    output_path: Path | None = None,
) -> dict[str, Any]:
    monitor = TrialMonitor()
    output_path = output_path or _default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_runs = (duration_hours // interval_hours) + 1
    if dry_run:
        total_runs = min(total_runs, 3)

    print(f"Starting trial: {total_runs} runs, interval={interval_hours}h, dry_run={dry_run}")

    for i in range(total_runs):
        run_id = f"trial-{i + 1:03d}"
        print(f"[{i + 1}/{total_runs}] Running {run_id}...")

        record = simulate_trial_run(run_id, dry_run=dry_run)
        monitor.add(record)

        print(f"  Status: {record.status.value}, Duration: {record.duration_ms}ms, SKUs: {record.skus_processed}")

        if not dry_run and i < total_runs - 1:
            print(f"  Sleeping {interval_hours}h until next run...")
            time.sleep(interval_hours * 3600)

    summary = monitor.build_summary()
    summary["trial_config"] = {
        "interval_hours": interval_hours,
        "duration_hours": duration_hours,
        "dry_run": dry_run,
        "started_at": monitor.get_records()[0].started_at.isoformat() if monitor.get_records() else None,
        "ended_at": monitor.get_records()[-1].started_at.isoformat() if monitor.get_records() else None,
    }
    summary["records"] = [r.to_dict() for r in monitor.get_records()]

    output_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nTrial complete: {summary['success_count']}/{summary['total_runs']} runs passed")
    print(f"Availability: {summary['availability']:.2%}")
    print(f"P95 Latency: {summary['p95_latency_ms']}ms")
    print(f"Output: {output_path}")

    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MV5-05 7x24 trial runner.")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_HOURS, help="Hours between runs")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_HOURS, help="Total trial duration in hours")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without real execution")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_trial(
        interval_hours=args.interval,
        duration_hours=args.duration,
        dry_run=args.dry_run,
        output_path=args.output,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
