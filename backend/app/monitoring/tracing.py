"""
ArmPilot-AI — Distributed Tracing
Provides a lightweight context-manager-based tracer that wraps OpenTelemetry
when available and falls back to no-op spans otherwise.
"""

from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional, TypeVar

from app.core.logger import logger
from app.monitoring.telemetry import telemetry_manager

F = TypeVar("F", bound=Callable[..., Any])


class Span:
    """A tracing span — lightweight wrapper around OTel spans."""

    __slots__ = ("name", "attributes", "_start", "_otel_span", "error")

    def __init__(self, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        self.name = name
        self.attributes = attributes or {}
        self._start = 0.0
        self._otel_span: Optional[Any] = None
        self.error: Optional[str] = None

    def start(self) -> None:
        self._start = time.perf_counter()
        tracer = telemetry_manager.get_tracer()
        if tracer is not None and hasattr(tracer, "start_as_current_span"):
            self._otel_span = tracer.start_as_current_span(self.name)
            if hasattr(self._otel_span, "__enter__"):
                self._otel_span.__enter__()
            # Set attributes on the OTel span
            if hasattr(self._otel_span, "set_attribute"):
                for k, v in self.attributes.items():
                    try:
                        self._otel_span.set_attribute(k, str(v))
                    except Exception:
                        pass

    def finish(self, error: Optional[str] = None) -> float:
        """Finish the span and return elapsed time in seconds."""
        elapsed = time.perf_counter() - self._start
        if error:
            self.error = error
            if self._otel_span is not None and hasattr(self._otel_span, "set_status"):
                try:
                    from opentelemetry.trace import StatusCode
                    self._otel_span.set_status(StatusCode.ERROR, error)
                except Exception:
                    pass
        if self._otel_span is not None and hasattr(self._otel_span, "__exit__"):
            try:
                self._otel_span.__exit__(None, None, None)
            except Exception:
                pass
        return elapsed

    def __enter__(self) -> "Span":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        error = str(exc_val) if exc_val else None
        elapsed = self.finish(error)
        if error:
            logger.warning("Span %s failed (%.3fs): %s", self.name, elapsed, error)
        else:
            logger.debug("Span %s completed in %.3fs", self.name, elapsed)


def create_span(
    name: str,
    attributes: Optional[dict[str, Any]] = None,
) -> Span:
    """Create a new tracing span."""
    return Span(name, attributes)


@contextmanager
def trace_operation(
    name: str,
    *,
    record_duration: bool = True,
    **attributes: Any,
) -> Generator[Span, None, None]:
    """Context manager for tracing a block of code."""
    span = create_span(name, attributes)
    with span:
        yield span
        if record_duration:
            elapsed = time.perf_counter() - span._start
            logger.debug("Trace %s: %.3fs", name, elapsed)


def traced(
    name: Optional[str] = None,
    *,
    attributes: Optional[dict[str, Any]] = None,
) -> Callable[[F], F]:
    """Decorator that traces a function call as a span."""

    def decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attrs = dict(attributes or {})
            # Try to capture function arguments as attributes
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            for k, v in bound.arguments.items():
                if isinstance(v, (str, int, float, bool)):
                    attrs[f"arg.{k}"] = v

            with trace_operation(span_name, **attrs) as span:
                result = func(*args, **kwargs)
                return result

        return wrapper  # type: ignore[return-value]

    return decorator


class TracingMiddleware:
    """FastAPI middleware that creates a span for each request."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        span_name = f"HTTP {method} {path}"

        with trace_operation(
            span_name,
            http_method=method,
            http_path=path,
        ):
            await self.app(scope, receive, send)
