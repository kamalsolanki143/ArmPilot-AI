"""
ArmPilot-AI — Throughput Measurement
Tracks token and request throughput during inference.
"""

from __future__ import annotations

import time
from typing import Any


class ThroughputTracker:
    """Tracks token and request throughput over a measurement window."""

    def __init__(self) -> None:
        self._total_tokens: int = 0
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._start_time: float | None = None
        self._timestamps: list[float] = []

    def start(self) -> None:
        """Start the throughput measurement window."""
        self._start_time = time.perf_counter()
        self._timestamps = []

    def record_request(self, tokens: int, success: bool = True) -> None:
        """Record a completed request."""
        self._timestamps.append(time.perf_counter())
        self._total_requests += 1
        if success:
            self._total_tokens += tokens
        else:
            self._total_errors += 1

    def elapsed_seconds(self) -> float:
        """Return elapsed time since start."""
        if self._start_time is None:
            return 0.0
        return time.perf_counter() - self._start_time

    def summary(self) -> dict[str, Any]:
        """Return throughput statistics."""
        duration = self.elapsed_seconds()
        successful = self._total_requests - self._total_errors

        tps = round(self._total_tokens / duration, 2) if duration > 0 else 0.0
        rps = round(successful / duration, 2) if duration > 0 else 0.0

        # Inter-request intervals
        avg_interval_ms: float | None = None
        if len(self._timestamps) > 1:
            intervals = [
                self._timestamps[i] - self._timestamps[i - 1]
                for i in range(1, len(self._timestamps))
            ]
            avg_interval_ms = round((sum(intervals) / len(intervals)) * 1000, 2)

        return {
            "total_tokens": self._total_tokens,
            "total_requests": self._total_requests,
            "successful_requests": successful,
            "failed_requests": self._total_errors,
            "duration_seconds": round(duration, 2),
            "tokens_per_second": tps,
            "requests_per_second": rps,
            "avg_request_interval_ms": avg_interval_ms,
        }

    def reset(self) -> None:
        """Reset all counters."""
        self._total_tokens = 0
        self._total_requests = 0
        self._total_errors = 0
        self._start_time = None
        self._timestamps.clear()


def measure_throughput(
    generate_fn,
    prompt: str,
    max_tokens: int,
    num_requests: int = 10,
) -> dict[str, Any]:
    """
    Measure token and request throughput over multiple sequential requests.

    Args:
        generate_fn: Callable(prompt, max_tokens) that triggers inference.
        prompt: The prompt to send.
        max_tokens: Max tokens to generate per request.
        num_requests: Number of requests to run.

    Returns:
        Dictionary of throughput statistics.
    """
    tracker = ThroughputTracker()
    tracker.start()

    for _ in range(num_requests):
        try:
            result = generate_fn(prompt=prompt, max_tokens=max_tokens)
            tokens = result.get("completion_tokens", 0) if isinstance(result, dict) else 0
            tracker.record_request(tokens, success=True)
        except Exception:
            tracker.record_request(0, success=False)

    return tracker.summary()
