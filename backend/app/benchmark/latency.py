"""
ArmPilot-AI — Latency Measurement
Collects and analyzes inference latency metrics.
"""

from __future__ import annotations

import statistics
import time
from typing import Any


class LatencyCollector:
    """Collects latency samples and computes percentile statistics."""

    def __init__(self) -> None:
        self._samples_ms: list[float] = []
        self._start_time: float | None = None

    def start(self) -> None:
        """Start the latency timer."""
        self._start_time = time.perf_counter()

    def record(self, latency_ms: float) -> None:
        """Record a latency sample in milliseconds."""
        self._samples_ms.append(latency_ms)

    def stop(self) -> float:
        """Stop the timer and return elapsed time in ms."""
        if self._start_time is None:
            return 0.0
        elapsed_ms = (time.perf_counter() - self._start_time) * 1000
        self._samples_ms.append(elapsed_ms)
        self._start_time = None
        return elapsed_ms

    @property
    def count(self) -> int:
        return len(self._samples_ms)

    @property
    def samples(self) -> list[float]:
        return list(self._samples_ms)

    def reset(self) -> None:
        self._samples_ms.clear()
        self._start_time = None

    def summary(self) -> dict[str, Any]:
        """Return a summary of latency statistics."""
        if not self._samples_ms:
            return {
                "count": 0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "stddev_ms": 0.0,
                "p50_ms": 0.0,
                "p75_ms": 0.0,
                "p90_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
            }

        s = sorted(self._samples_ms)
        return {
            "count": len(s),
            "avg_ms": round(statistics.mean(s), 2),
            "min_ms": round(s[0], 2),
            "max_ms": round(s[-1], 2),
            "stddev_ms": round(statistics.stdev(s), 2) if len(s) > 1 else 0.0,
            "p50_ms": round(_percentile(s, 50), 2),
            "p75_ms": round(_percentile(s, 75), 2),
            "p90_ms": round(_percentile(s, 90), 2),
            "p95_ms": round(_percentile(s, 95), 2),
            "p99_ms": round(_percentile(s, 99), 2),
        }


def _percentile(sorted_data: list[float], p: float) -> float:
    """Compute the p-th percentile using linear interpolation."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


def measure_inference_latency(
    generate_fn,
    prompt: str,
    max_tokens: int,
    iterations: int = 1,
) -> dict[str, Any]:
    """
    Run generate_fn multiple times and return latency stats.

    Args:
        generate_fn: Callable(prompt, max_tokens) that triggers inference.
        prompt: The prompt to send.
        max_tokens: Max tokens to generate.
        iterations: Number of measurement iterations.

    Returns:
        Dictionary of latency statistics.
    """
    collector = LatencyCollector()
    for _ in range(iterations):
        collector.start()
        generate_fn(prompt=prompt, max_tokens=max_tokens)
        collector.stop()
    return collector.summary()
