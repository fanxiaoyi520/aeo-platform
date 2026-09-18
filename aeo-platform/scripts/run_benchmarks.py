"""P7-01: Run API performance benchmarks on key endpoints."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark_api import print_summary, run_benchmark


async def main() -> None:
    """Run benchmarks on all key API endpoints."""
    base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    api_key = os.environ.get("AUTH_API_KEY", "dev-api-key-change-in-production")
    headers = {"Authorization": f"Bearer {api_key}"}

    print("\n" + "=" * 80)
    print("AEO Platform API Performance Benchmark")
    print("=" * 80)
    print(f"Base URL: {base_url}")
    print("Iterations: 100 per endpoint")
    print("Concurrency: 10")
    print("=" * 80)

    endpoints = [
        ("/api/v1/health", "GET", None),
        ("/api/v1/agents", "GET", None),
        ("/api/v1/business-metrics/dashboard", "GET", None),
        ("/api/v1/analytics/report", "GET", None),
        ("/api/v1/billing/plans", "GET", None),
    ]

    summaries = []
    for endpoint, method, _ in endpoints:
        print(f"\nBenchmarking {method} {endpoint}...")
        summary = await run_benchmark(
            base_url=base_url,
            endpoint=endpoint,
            method=method,
            headers=headers,
            iterations=100,
            concurrency=10,
        )
        summaries.append(summary)
        print_summary(summary)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'Endpoint':<50} {'P95 (ms)':<15} {'Success Rate':<15}")
    print("-" * 80)
    for summary in summaries:
        endpoint_str = f"{summary.endpoint:<50}"
        p95_str = f"{summary.p95_response_time_ms:<15.2f}"
        success_str = f"{summary.success_rate:<15.1f}%"
        print(f"{endpoint_str} {p95_str} {success_str}")
    print("=" * 80)

    # Check SLA compliance
    print("\nSLA Compliance Check:")
    sla_violations = []
    for summary in summaries:
        if summary.p95_response_time_ms > 200:
            sla_violations.append(
                f"  ❌ {summary.endpoint}: P95 = {summary.p95_response_time_ms:.2f}ms (> 200ms)"
            )
        else:
            print(f"  ✅ {summary.endpoint}: P95 = {summary.p95_response_time_ms:.2f}ms (≤ 200ms)")

    if sla_violations:
        print("\nSLA Violations:")
        for violation in sla_violations:
            print(violation)
        print("\n⚠️  Performance optimization needed!")
    else:
        print("\n✅ All endpoints meet SLA (P95 ≤ 200ms)")


if __name__ == "__main__":
    asyncio.run(main())
