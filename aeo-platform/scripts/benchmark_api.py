"""P7-01: API performance benchmarking tool."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class BenchmarkResult:
    """Result of a single API benchmark."""

    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error: str | None = None


@dataclass
class BenchmarkSummary:
    """Summary of benchmark results."""

    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    results: list[BenchmarkResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


async def benchmark_endpoint(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    json_data: dict[str, Any] | None = None,
) -> BenchmarkResult:
    """Benchmark a single API endpoint."""
    start = time.perf_counter()
    try:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=json_data)
        else:
            msg = f"Unsupported method: {method}"
            raise ValueError(msg)

        elapsed_ms = (time.perf_counter() - start) * 1000
        return BenchmarkResult(
            endpoint=url,
            method=method,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            success=200 <= response.status_code < 300,
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return BenchmarkResult(
            endpoint=url,
            method=method,
            status_code=0,
            response_time_ms=elapsed_ms,
            success=False,
            error=str(exc),
        )


def _percentile(values: list[float], percentile: float) -> float:
    """Calculate percentile from a list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]


async def run_benchmark(
    base_url: str,
    endpoint: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_data: dict[str, Any] | None = None,
    iterations: int = 100,
    concurrency: int = 10,
) -> BenchmarkSummary:
    """Run benchmark for an endpoint with multiple iterations."""
    url = f"{base_url}{endpoint}"
    results: list[BenchmarkResult] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_benchmark() -> BenchmarkResult:
            async with semaphore:
                return await benchmark_endpoint(client, method, url, headers, json_data)

        tasks = [bounded_benchmark() for _ in range(iterations)]
        results = await asyncio.gather(*tasks)

    response_times = [r.response_time_ms for r in results if r.success]
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    return BenchmarkSummary(
        endpoint=endpoint,
        total_requests=len(results),
        successful_requests=len(successful),
        failed_requests=len(failed),
        avg_response_time_ms=sum(response_times) / len(response_times) if response_times else 0.0,
        min_response_time_ms=min(response_times) if response_times else 0.0,
        max_response_time_ms=max(response_times) if response_times else 0.0,
        p50_response_time_ms=_percentile(response_times, 50),
        p95_response_time_ms=_percentile(response_times, 95),
        p99_response_time_ms=_percentile(response_times, 99),
        results=list(results),
    )


def print_summary(summary: BenchmarkSummary) -> None:
    """Print benchmark summary in a formatted way."""
    print(f"\n{'=' * 80}")
    print(f"Endpoint: {summary.endpoint}")
    print(f"{'=' * 80}")
    print(f"Total Requests:      {summary.total_requests}")
    print(f"Successful:          {summary.successful_requests} ({summary.success_rate:.1f}%)")
    print(f"Failed:              {summary.failed_requests}")
    print("\nResponse Times (ms):")
    print(f"  Average:           {summary.avg_response_time_ms:.2f}")
    print(f"  Min:               {summary.min_response_time_ms:.2f}")
    print(f"  Max:               {summary.max_response_time_ms:.2f}")
    print(f"  P50:               {summary.p50_response_time_ms:.2f}")
    print(f"  P95:               {summary.p95_response_time_ms:.2f}")
    print(f"  P99:               {summary.p99_response_time_ms:.2f}")
    print(f"{'=' * 80}\n")
