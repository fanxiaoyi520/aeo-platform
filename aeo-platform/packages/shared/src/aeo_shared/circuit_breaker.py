"""P7-05: Circuit breaker pattern for fault tolerance."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exceptions: tuple[type[Exception], ...] = (Exception,)
    name: str = "default"


@dataclass
class CircuitBreakerState:
    failures: int = 0
    last_failure_time: float = 0.0
    state: CircuitState = CircuitState.CLOSED
    success_count: int = 0
    failure_count: int = 0


class CircuitBreakerOpen(Exception):
    def __init__(self, name: str, remaining_time: float) -> None:
        self.name = name
        self.remaining_time = remaining_time
        super().__init__(f"Circuit breaker '{name}' is open, {remaining_time:.1f}s until retry")


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()
        self._lock = False

    @property
    def state(self) -> CircuitState:
        if self._state.state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._state.last_failure_time
            if elapsed >= self.config.recovery_timeout:
                self._state.state = CircuitState.HALF_OPEN
        return self._state.state

    @property
    def failures(self) -> int:
        return self._state.failures

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if self.state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._state.last_failure_time
            remaining = self.config.recovery_timeout - elapsed
            raise CircuitBreakerOpen(self.config.name, max(0, remaining))

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exceptions:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self._state.success_count += 1
        if self._state.state == CircuitState.HALF_OPEN:
            self._state.state = CircuitState.CLOSED
            self._state.failures = 0

    def _on_failure(self) -> None:
        self._state.failures += 1
        self._state.failure_count += 1
        self._state.last_failure_time = time.monotonic()

        if self._state.failures >= self.config.failure_threshold:
            self._state.state = CircuitState.OPEN

    def reset(self) -> None:
        self._state = CircuitBreakerState()

    def get_stats(self) -> dict[str, Any]:
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failures": self._state.failures,
            "success_count": self._state.success_count,
            "failure_count": self._state.failure_count,
            "failure_threshold": self.config.failure_threshold,
            "recovery_timeout": self.config.recovery_timeout,
        }


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        if name not in self._breakers:
            cfg = config or CircuitBreakerConfig(name=name)
            self._breakers[name] = CircuitBreaker(cfg)
        return self._breakers[name]

    def get(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def reset_all(self) -> None:
        for breaker in self._breakers.values():
            breaker.reset()

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}


DEFAULT_REGISTRY = CircuitBreakerRegistry()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exceptions=expected_exceptions,
        name=name,
    )
    breaker = DEFAULT_REGISTRY.get_or_create(name, config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
