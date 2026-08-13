"""
ArmPilot-AI — Prometheus Metrics
Exposes application metrics via prometheus_client for scraping.
"""

from __future__ import annotations

import time
from typing import Optional

from app.core.logger import logger

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Summary,
        REGISTRY,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

    # Provide stub classes so the rest of the app can import without crashing
    class _StubMetric:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def inc(self, *args: object, **kwargs: object) -> None:
            pass

        def dec(self, *args: object, **kwargs: object) -> None:
            pass

        def set(self, *args: object, **kwargs: object) -> None:
            pass

        def observe(self, *args: object, **kwargs: object) -> None:
            pass

        def labels(self, *args: object, **kwargs: object) -> "_StubMetric":
            return self

        def time(self) -> "TimerStub":
            return TimerStub()

    class TimerStub:
        def __enter__(self) -> "TimerStub":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    Counter = _StubMetric  # type: ignore[misc]
    Gauge = _StubMetric  # type: ignore[misc]
    Histogram = _StubMetric  # type: ignore[misc]
    Summary = _StubMetric  # type: ignore[misc]


# ── Inference Metrics ────────────────────────────────────────────────────

INFERENCE_REQUESTS_TOTAL = Counter(
    "armpilot_inference_requests_total",
    "Total inference requests",
    ["model", "status"],
)

INFERENCE_LATENCY_SECONDS = Histogram(
    "armpilot_inference_latency_seconds",
    "Inference request latency in seconds",
    ["model"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

INFERENCE_TOKENS_TOTAL = Counter(
    "armpilot_inference_tokens_total",
    "Total tokens generated",
    ["model"],
)

INFERENCE_TOKENS_PER_SECOND = Gauge(
    "armpilot_inference_tokens_per_second",
    "Current tokens per second throughput",
    ["model"],
)

INFERENCE_TTFT_SECONDS = Summary(
    "armpilot_inference_ttft_seconds",
    "Time to first token",
    ["model"],
)

ACTIVE_REQUESTS = Gauge(
    "armpilot_active_requests",
    "Number of currently active inference requests",
)

MODEL_LOADED = Gauge(
    "armpilot_model_loaded",
    "Whether a model is currently loaded (1=yes, 0=no)",
)

MODEL_MEMORY_MB = Gauge(
    "armpilot_model_memory_mb",
    "Memory used by the loaded model in MB",
)

# ── Benchmark Metrics ───────────────────────────────────────────────────

BENCHMARK_RUNS_TOTAL = Counter(
    "armpilot_benchmark_runs_total",
    "Total benchmark runs",
    ["status"],
)

BENCHMARK_DURATION_SECONDS = Histogram(
    "armpilot_benchmark_duration_seconds",
    "Benchmark run duration in seconds",
    buckets=(10, 30, 60, 120, 300, 600),
)

# ── System Metrics ──────────────────────────────────────────────────────

SYSTEM_CPU_PERCENT = Gauge(
    "armpilot_system_cpu_percent",
    "System CPU utilization percentage",
)

SYSTEM_MEMORY_PERCENT = Gauge(
    "armpilot_system_memory_percent",
    "System memory utilization percentage",
)

SYSTEM_MEMORY_USED_MB = Gauge(
    "armpilot_system_memory_used_mb",
    "System memory used in MB",
)

# ── Cache Metrics ───────────────────────────────────────────────────────

CACHE_HITS_TOTAL = Counter(
    "armpilot_cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

CACHE_MISSES_TOTAL = Counter(
    "armpilot_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

CACHE_SIZE = Gauge(
    "armpilot_cache_size",
    "Current number of entries in cache",
    ["cache_type"],
)


def record_inference_request(model: str, status: str, duration: float, tokens: int = 0) -> None:
    """Record metrics for a completed inference request."""
    INFERENCE_REQUESTS_TOTAL.labels(model=model, status=status).inc()
    INFERENCE_LATENCY_SECONDS.labels(model=model).observe(duration)
    if tokens > 0:
        INFERENCE_TOKENS_TOTAL.labels(model=model).inc(tokens)
        if duration > 0:
            INFERENCE_TOKENS_PER_SECOND.labels(model=model).set(tokens / duration)


def record_inference_ttft(model: str, ttft: float) -> None:
    """Record time-to-first-token."""
    INFERENCE_TTFT_SECONDS.labels(model=model).observe(ttft)


def update_system_metrics(cpu_percent: float, memory_percent: float, memory_used_mb: float) -> None:
    """Push current system metrics."""
    SYSTEM_CPU_PERCENT.set(cpu_percent)
    SYSTEM_MEMORY_PERCENT.set(memory_percent)
    SYSTEM_MEMORY_USED_MB.set(memory_used_mb)


def update_model_state(loaded: bool, memory_mb: float = 0.0) -> None:
    """Update model loaded state and memory."""
    MODEL_LOADED.set(1 if loaded else 0)
    if loaded:
        MODEL_MEMORY_MB.set(memory_mb)


def record_cache_hit(cache_type: str) -> None:
    CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()


def update_cache_size(cache_type: str, size: int) -> None:
    CACHE_SIZE.labels(cache_type=cache_type).set(size)


def get_metrics() -> bytes:
    """Return Prometheus-compatible metrics text."""
    if not HAS_PROMETHEUS:
        return b"# prometheus_client not installed\n"
    return generate_latest(REGISTRY)


def get_content_type() -> str:
    if not HAS_PROMETHEUS:
        return "text/plain"
    return CONTENT_TYPE_LATEST
