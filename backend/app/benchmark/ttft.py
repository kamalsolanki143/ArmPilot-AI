"""
ArmPilot-AI — Time-To-First-Token (TTFT) Measurement
Measures the time until the first token is produced during streaming inference.
"""

from __future__ import annotations

import time
from typing import Any


class TTFTCollector:
    """Collects time-to-first-token measurements from streaming inference."""

    def __init__(self) -> None:
        self._samples_ms: list[float] = []

    def measure_stream(self, stream) -> tuple[Any, float | None]:
        """
        Iterate a streaming generator, capture TTFT, and return (tokens, ttft_ms).

        Args:
            stream: An iterable yielding dicts with optional 'is_first', 'ttft_ms' keys.

        Returns:
            Tuple of (token_count, ttft_ms or None).
        """
        ttft_ms: float | None = None
        token_count = 0

        for chunk in stream:
            token_count += 1
            if ttft_ms is None and chunk.get("is_first") and "ttft_ms" in chunk:
                ttft_ms = chunk["ttft_ms"]
            if ttft_ms is None and chunk.get("is_first"):
                # Fallback: if runtime doesn't provide ttft_ms, we can't compute it here
                pass

        if ttft_ms is not None:
            self._samples_ms.append(ttft_ms)

        return token_count, ttft_ms

    def record(self, ttft_ms: float) -> None:
        """Manually record a TTFT measurement."""
        self._samples_ms.append(ttft_ms)

    @property
    def count(self) -> int:
        return len(self._samples_ms)

    def summary(self) -> dict[str, Any]:
        """Return TTFT statistics."""
        if not self._samples_ms:
            return {
                "count": 0,
                "avg_ms": None,
                "min_ms": None,
                "max_ms": None,
                "p50_ms": None,
                "p95_ms": None,
            }

        s = sorted(self._samples_ms)
        return {
            "count": len(s),
            "avg_ms": round(sum(s) / len(s), 2),
            "min_ms": round(s[0], 2),
            "max_ms": round(s[-1], 2),
            "p50_ms": round(_percentile(s, 50), 2),
            "p95_ms": round(_percentile(s, 95), 2),
        }

    def reset(self) -> None:
        self._samples_ms.clear()


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


def measure_ttft(
    generate_stream_fn,
    prompt: str,
    max_tokens: int,
    iterations: int = 1,
) -> dict[str, Any]:
    """
    Measure time-to-first-token over multiple streaming requests.

    Args:
        generate_stream_fn: Callable(prompt, max_tokens) returning a stream iterable.
        prompt: The prompt to send.
        max_tokens: Max tokens to generate.
        iterations: Number of measurement iterations.

    Returns:
        Dictionary of TTFT statistics.
    """
    collector = TTFTCollector()
    for _ in range(iterations):
        stream = generate_stream_fn(prompt=prompt, max_tokens=max_tokens)
        collector.measure_stream(stream)
    return collector.summary()
