"""P7-06: OpenTelemetry tracing utilities."""

from __future__ import annotations

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    start_time: float
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({"name": name, "attributes": attributes or {}, "timestamp": time.time()})

    def set_status(self, status: str) -> None:
        self.status = status

    def end(self) -> None:
        self.end_time = time.time()


@dataclass
class Tracer:
    name: str
    spans: list[Span] = field(default_factory=list)

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        span = Span(name=name, start_time=time.time(), attributes=attributes or {})
        self.spans.append(span)
        return span

    @contextmanager
    def span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> Generator[Span, None, None]:
        span = self.start_span(name, attributes)
        try:
            yield span
            span.set_status("ok")
        except Exception as e:
            span.set_status("error")
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.type", type(e).__name__)
            raise
        finally:
            span.end()

    def get_spans(self) -> list[Span]:
        return self.spans

    def clear(self) -> None:
        self.spans.clear()


_TRACERS: dict[str, Tracer] = {}


def get_tracer(name: str) -> Tracer:
    if name not in _TRACERS:
        _TRACERS[name] = Tracer(name=name)
    return _TRACERS[name]


def trace_operation(
    operation_name: str,
    tracer_name: str = "default",
    attributes: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer(tracer_name)
            with tracer.span(operation_name, attributes) as span:
                span.set_attribute("function", func.__name__)
                result = func(*args, **kwargs)
                return result

        return wrapper

    return decorator


def get_all_tracers() -> dict[str, Tracer]:
    return _TRACERS


def reset_all_tracers() -> None:
    for tracer in _TRACERS.values():
        tracer.clear()
