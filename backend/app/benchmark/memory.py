"""
ArmPilot-AI — Memory Usage Tracking
Tracks memory consumption during benchmark and inference operations.
"""

from __future__ import annotations

import os
from typing import Any

import psutil


def get_process_memory() -> dict[str, Any]:
    """Get current process memory usage."""
    try:
        proc = psutil.Process(os.getpid())
        mem_info = proc.memory_info()
        return {
            "rss_mb": round(mem_info.rss / (1024 ** 2), 2),
            "vms_mb": round(mem_info.vms / (1024 ** 2), 2),
            "percent": proc.memory_percent(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {"rss_mb": 0.0, "vms_mb": 0.0, "percent": 0.0}


def get_system_memory() -> dict[str, Any]:
    """Get system-wide memory usage."""
    mem = psutil.virtual_memory()
    return {
        "total_mb": round(mem.total / (1024 ** 2), 1),
        "available_mb": round(mem.available / (1024 ** 2), 1),
        "used_mb": round(mem.used / (1024 ** 2), 1),
        "used_percent": mem.percent,
    }


class MemoryTracker:
    """Tracks memory usage over time with peak/average calculations."""

    def __init__(self) -> None:
        self._samples: list[dict[str, float]] = []
        self._baseline_rss_mb: float = 0.0

    def snapshot(self) -> dict[str, float]:
        """Take a memory snapshot and return process memory."""
        mem = get_process_memory()
        self._samples.append(mem)
        return mem

    def set_baseline(self) -> None:
        """Record baseline memory before a benchmark starts."""
        mem = get_process_memory()
        self._baseline_rss_mb = mem.get("rss_mb", 0.0)

    def peak_rss_mb(self) -> float:
        """Return the peak RSS observed across all snapshots."""
        if not self._samples:
            return 0.0
        return max(s.get("rss_mb", 0.0) for s in self._samples)

    def avg_rss_mb(self) -> float:
        """Return the average RSS observed across all snapshots."""
        if not self._samples:
            return 0.0
        return round(sum(s.get("rss_mb", 0.0) for s in self._samples) / len(self._samples), 2)

    def delta_mb(self) -> float:
        """Return the difference between current peak and baseline."""
        peak = self.peak_rss_mb()
        return round(peak - self._baseline_rss_mb, 2) if self._baseline_rss_mb > 0 else 0.0

    def summary(self) -> dict[str, Any]:
        """Return a memory usage summary."""
        return {
            "baseline_rss_mb": round(self._baseline_rss_mb, 2),
            "peak_rss_mb": self.peak_rss_mb(),
            "avg_rss_mb": self.avg_rss_mb(),
            "delta_mb": self.delta_mb(),
            "snapshots_count": len(self._samples),
            "system": get_system_memory(),
        }

    def reset(self) -> None:
        self._samples.clear()
        self._baseline_rss_mb = 0.0
