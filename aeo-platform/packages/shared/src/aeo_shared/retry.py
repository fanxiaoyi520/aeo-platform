"""P7-04: Unified retry strategies with configurable policies."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    min_wait_seconds: float = 1.0
    max_wait_seconds: float = 10.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)

    def to_tenacity_retry(self) -> retry:
        wait = wait_exponential(
            multiplier=self.min_wait_seconds,
            max=self.max_wait_seconds,
            exp_base=self.exponential_base,
        )
        if self.jitter:
            wait = wait + wait_random(0, 1)

        return retry(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait,
            retry=retry_if_exception_type(self.retryable_exceptions),
            reraise=True,
        )


DEFAULT_POLICY = RetryPolicy()

DATABASE_POLICY = RetryPolicy(
    max_attempts=3,
    min_wait_seconds=0.5,
    max_wait_seconds=5.0,
    retryable_exceptions=(Exception,),
)

EXTERNAL_API_POLICY = RetryPolicy(
    max_attempts=3,
    min_wait_seconds=1.0,
    max_wait_seconds=30.0,
    retryable_exceptions=(Exception,),
)

LLM_POLICY = RetryPolicy(
    max_attempts=2,
    min_wait_seconds=2.0,
    max_wait_seconds=20.0,
    retryable_exceptions=(Exception,),
)


def with_retry(
    func: Callable[..., T],
    policy: RetryPolicy | None = None,
    before_sleep: Callable[[RetryCallState], Any] | None = None,
) -> Callable[..., T]:
    retry_decorator = policy.to_tenacity_retry() if policy else DEFAULT_POLICY.to_tenacity_retry()
    decorated = retry_decorator(func)
    if before_sleep:
        decorated = retry(
            stop=stop_after_attempt(policy.max_attempts if policy else DEFAULT_POLICY.max_attempts),
            wait=wait_exponential(
                multiplier=policy.min_wait_seconds if policy else DEFAULT_POLICY.min_wait_seconds,
                max=policy.max_wait_seconds if policy else DEFAULT_POLICY.max_wait_seconds,
            ),
            before_sleep=before_sleep,
        )(func)
    return decorated


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    jitter: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    policy = RetryPolicy(
        max_attempts=max_attempts,
        min_wait_seconds=min_wait,
        max_wait_seconds=max_wait,
        jitter=jitter,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return policy.to_tenacity_retry()(func)

    return decorator


def calculate_backoff(attempt: int, base: float = 2.0, max_wait: float = 60.0) -> float:
    wait = min(base**attempt, max_wait)
    jitter = random.uniform(0, wait * 0.1)
    return wait + jitter
