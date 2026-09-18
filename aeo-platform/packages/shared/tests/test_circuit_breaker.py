"""P7-05: Tests for circuit breaker pattern."""

from __future__ import annotations

import time

import pytest
from aeo_shared.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitBreakerRegistry,
    CircuitState,
    circuit_breaker,
)


class TestCircuitBreaker:
    def test_initial_state_closed(self) -> None:
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED

    def test_successful_call(self) -> None:
        breaker = CircuitBreaker()
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_failure_increments_counter(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert breaker.failures == 3

    def test_opens_after_threshold(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker(config)

        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert breaker.state == CircuitState.OPEN

    def test_open_circuit_raises_immediately(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=10.0)
        breaker = CircuitBreaker(config)

        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        with pytest.raises(CircuitBreakerOpen) as exc_info:
            breaker.call(lambda: "should not run")

        assert exc_info.value.remaining_time > 0

    def test_half_open_after_recovery_timeout(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        breaker = CircuitBreaker(config)

        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert breaker.state == CircuitState.OPEN
        time.sleep(0.15)
        assert breaker.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        breaker = CircuitBreaker(config)

        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        time.sleep(0.15)
        result = breaker.call(lambda: "recovered")

        assert result == "recovered"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failures == 0

    def test_half_open_failure_reopens_circuit(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        breaker = CircuitBreaker(config)

        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        time.sleep(0.15)
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail again")))

        assert breaker.state == CircuitState.OPEN

    def test_reset(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker(config)

        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        breaker.reset()
        assert breaker.failures == 0
        assert breaker.state == CircuitState.CLOSED

    def test_get_stats(self) -> None:
        config = CircuitBreakerConfig(name="test", failure_threshold=3)
        breaker = CircuitBreaker(config)

        breaker.call(lambda: "success")
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        stats = breaker.get_stats()
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["success_count"] == 1
        assert stats["failure_count"] == 1


class TestCircuitBreakerRegistry:
    def test_get_or_create(self) -> None:
        registry = CircuitBreakerRegistry()
        breaker1 = registry.get_or_create("test")
        breaker2 = registry.get_or_create("test")

        assert breaker1 is breaker2

    def test_get_nonexistent(self) -> None:
        registry = CircuitBreakerRegistry()
        assert registry.get("nonexistent") is None

    def test_reset_all(self) -> None:
        registry = CircuitBreakerRegistry()
        b1 = registry.get_or_create("b1")
        b2 = registry.get_or_create("b2")

        b1._state.failures = 5
        b2._state.failures = 3

        registry.reset_all()

        assert b1.failures == 0
        assert b2.failures == 0

    def test_get_all_stats(self) -> None:
        registry = CircuitBreakerRegistry()
        registry.get_or_create("b1")
        registry.get_or_create("b2")

        stats = registry.get_all_stats()
        assert "b1" in stats
        assert "b2" in stats


class TestCircuitBreakerDecorator:
    def test_decorator_success(self) -> None:
        @circuit_breaker("test", failure_threshold=2)
        def func() -> str:
            return "ok"

        assert func() == "ok"

    def test_decorator_failure(self) -> None:
        @circuit_breaker("test", failure_threshold=2, recovery_timeout=0.1)
        def func() -> str:
            raise ValueError("fail")

        with pytest.raises(ValueError):
            func()

        with pytest.raises(ValueError):
            func()

        with pytest.raises(CircuitBreakerOpen):
            func()
