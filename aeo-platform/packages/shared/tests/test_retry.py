"""P7-04: Tests for unified retry strategies."""

from __future__ import annotations

import pytest
from aeo_shared.retry import (
    DATABASE_POLICY,
    DEFAULT_POLICY,
    EXTERNAL_API_POLICY,
    LLM_POLICY,
    RetryPolicy,
    calculate_backoff,
    retry_with_backoff,
    with_retry,
)


class TestRetryPolicy:
    def test_default_policy_values(self) -> None:
        assert DEFAULT_POLICY.max_attempts == 3
        assert DEFAULT_POLICY.min_wait_seconds == 1.0
        assert DEFAULT_POLICY.max_wait_seconds == 10.0

    def test_database_policy(self) -> None:
        assert DATABASE_POLICY.max_attempts == 3
        assert DATABASE_POLICY.min_wait_seconds == 0.5

    def test_external_api_policy(self) -> None:
        assert EXTERNAL_API_POLICY.max_attempts == 3
        assert EXTERNAL_API_POLICY.max_wait_seconds == 30.0

    def test_llm_policy(self) -> None:
        assert LLM_POLICY.max_attempts == 2
        assert LLM_POLICY.min_wait_seconds == 2.0

    def test_custom_policy(self) -> None:
        policy = RetryPolicy(max_attempts=5, min_wait_seconds=2.0)
        assert policy.max_attempts == 5
        assert policy.min_wait_seconds == 2.0


class TestWithRetry:
    def test_successful_call_no_retry(self) -> None:
        call_count = 0

        def func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        wrapped = with_retry(func, DEFAULT_POLICY)
        result = wrapped()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self) -> None:
        call_count = 0

        def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "success"

        policy = RetryPolicy(max_attempts=3, min_wait_seconds=0.01, max_wait_seconds=0.1)
        wrapped = with_retry(func, policy)
        result = wrapped()

        assert result == "success"
        assert call_count == 3

    def test_max_attempts_exceeded(self) -> None:
        call_count = 0

        def func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("persistent error")

        policy = RetryPolicy(
            max_attempts=2,
            min_wait_seconds=0.01,
            max_wait_seconds=0.1,
            retryable_exceptions=(ValueError,),
        )
        wrapped = with_retry(func, policy)

        with pytest.raises(ValueError, match="persistent error"):
            wrapped()

        assert call_count == 2


class TestRetryWithBackoff:
    def test_decorator_syntax(self) -> None:
        call_count = 0

        @retry_with_backoff(max_attempts=2, min_wait=0.01, max_wait=0.1)
        def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("fail")
            return "ok"

        result = func()
        assert result == "ok"
        assert call_count == 2


class TestCalculateBackoff:
    def test_exponential_growth(self) -> None:
        wait1 = calculate_backoff(1, base=2.0, max_wait=60.0)
        wait2 = calculate_backoff(2, base=2.0, max_wait=60.0)
        wait3 = calculate_backoff(3, base=2.0, max_wait=60.0)

        assert 2.0 <= wait1 <= 2.2
        assert 4.0 <= wait2 <= 4.4
        assert 8.0 <= wait3 <= 8.8

    def test_max_wait_cap(self) -> None:
        wait = calculate_backoff(10, base=2.0, max_wait=10.0)
        assert wait <= 11.0

    def test_jitter_added(self) -> None:
        waits = [calculate_backoff(3, base=2.0, max_wait=60.0) for _ in range(10)]
        assert len(set(waits)) > 1
