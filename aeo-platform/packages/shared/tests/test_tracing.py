"""P7-06: Tests for tracing utilities."""

from __future__ import annotations

import time

import pytest
from aeo_shared.tracing import (
    Span,
    Tracer,
    get_all_tracers,
    get_tracer,
    reset_all_tracers,
    trace_operation,
)


class TestSpan:
    def test_span_creation(self) -> None:
        span = Span(name="test", start_time=time.time())
        assert span.name == "test"
        assert span.end_time is None
        assert span.status == "ok"

    def test_span_duration(self) -> None:
        start = time.time()
        span = Span(name="test", start_time=start)
        time.sleep(0.01)
        span.end()

        assert span.duration_ms >= 10
        assert span.end_time is not None

    def test_span_set_attribute(self) -> None:
        span = Span(name="test", start_time=time.time())
        span.set_attribute("key", "value")
        assert span.attributes["key"] == "value"

    def test_span_add_event(self) -> None:
        span = Span(name="test", start_time=time.time())
        span.add_event("event1", {"detail": "info"})

        assert len(span.events) == 1
        assert span.events[0]["name"] == "event1"
        assert span.events[0]["attributes"]["detail"] == "info"

    def test_span_set_status(self) -> None:
        span = Span(name="test", start_time=time.time())
        span.set_status("error")
        assert span.status == "error"


class TestTracer:
    def test_tracer_creation(self) -> None:
        tracer = Tracer(name="test")
        assert tracer.name == "test"
        assert len(tracer.spans) == 0

    def test_start_span(self) -> None:
        tracer = Tracer(name="test")
        span = tracer.start_span("operation")

        assert span.name == "operation"
        assert len(tracer.spans) == 1

    def test_span_context_manager(self) -> None:
        tracer = Tracer(name="test")

        with tracer.span("operation") as span:
            span.set_attribute("key", "value")

        assert span.end_time is not None
        assert span.status == "ok"
        assert span.attributes["key"] == "value"

    def test_span_context_manager_with_error(self) -> None:
        tracer = Tracer(name="test")

        with pytest.raises(ValueError), tracer.span("operation") as span:
            raise ValueError("test error")

        assert span.status == "error"
        assert span.attributes["error.message"] == "test error"
        assert span.attributes["error.type"] == "ValueError"

    def test_get_spans(self) -> None:
        tracer = Tracer(name="test")
        tracer.start_span("op1")
        tracer.start_span("op2")

        spans = tracer.get_spans()
        assert len(spans) == 2

    def test_clear(self) -> None:
        tracer = Tracer(name="test")
        tracer.start_span("op1")
        tracer.clear()

        assert len(tracer.spans) == 0


class TestGetTracer:
    def test_get_tracer_creates_new(self) -> None:
        reset_all_tracers()
        tracer = get_tracer("new_tracer")

        assert tracer.name == "new_tracer"
        assert "new_tracer" in get_all_tracers()

    def test_get_tracer_returns_same(self) -> None:
        reset_all_tracers()
        tracer1 = get_tracer("same")
        tracer2 = get_tracer("same")

        assert tracer1 is tracer2


class TestTraceOperation:
    def test_decorator_success(self) -> None:
        reset_all_tracers()

        @trace_operation("test_op", tracer_name="test")
        def func(x: int) -> int:
            return x * 2

        result = func(5)
        assert result == 10

        tracer = get_tracer("test")
        assert len(tracer.spans) == 1
        assert tracer.spans[0].name == "test_op"
        assert tracer.spans[0].attributes["function"] == "func"

    def test_decorator_with_attributes(self) -> None:
        reset_all_tracers()

        @trace_operation("test_op", tracer_name="test", attributes={"custom": "value"})
        def func() -> None:
            pass

        func()

        tracer = get_tracer("test")
        assert tracer.spans[0].attributes["custom"] == "value"


class TestResetAllTracers:
    def test_reset_all(self) -> None:
        reset_all_tracers()
        t1 = get_tracer("t1")
        t2 = get_tracer("t2")

        t1.start_span("op1")
        t2.start_span("op2")

        reset_all_tracers()

        assert len(t1.spans) == 0
        assert len(t2.spans) == 0
