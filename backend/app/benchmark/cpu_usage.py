"""
ArmPilot-AI — CPU Usage Tracking
Tracks CPU utilization during benchmark and inference operations.
"""

from __future__ import annotations

import os
from typing import Any

import psutil


def get_cpu_usage() -> dict[str, Any]:
    """Get current CPU utilization metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    per_core = psutil.cpu_percent(interval=0, percpu=True)
    cpu_freq = psutil.cpu_freq()

    return {
        "overall_percent": cpu_percent,
        "per_core_percent": per_core,
        "frequency_mhz": cpu_freq.current if cpu_freq else None,
        "logical_count": psutil.cpu_count(logical=True),
        "physical_count": psutil.cpu_count(logical=False),
    }


def get_process_cpu() -> dict[str, Any]:
    """Get CPU usage for the current process."""
    try:
        proc = psutil.Process(os.getpid())
        return {
            "pid": proc.pid,
            "cpu_percent": proc.cpu_percent(interval=0.1),
            "num_threads": proc.num_threads(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {"pid": os.getpid(), "cpu_percent": 0.0, "num_threads": 0}


class CPUTracker:
    """Tracks CPU usage over time with peak/average calculations."""

    def __init__(self) -> None:
        self._system_samples: list[float] = []
        self._process_samples: list[float] = []
        self._thread_counts: list[int] = []

    def snapshot(self) -> dict[str, Any]:
        """Take a CPU usage snapshot."""
        sys_cpu = get_cpu_usage()
        proc_cpu = get_process_cpu()

        self._system_samples.append(sys_cpu["overall_percent"])
        self._process_samples.append(proc_cpu["cpu_percent"])
        self._thread_counts.append(proc_cpu["num_threads"])

        return {
            "system_percent": sys_cpu["overall_percent"],
            "process_percent": proc_cpu["cpu_percent"],
            "threads": proc_cpu["num_threads"],
        }

    def avg_system_percent(self) -> float:
        """Return average system CPU usage."""
        if not self._system_samples:
            return 0.0
        return round(sum(self._system_samples) / len(self._system_samples), 1)

    def avg_process_percent(self) -> float:
        """Return average process CPU usage."""
        if not self._process_samples:
            return 0.0
        return round(sum(self._process_samples) / len(self._process_samples), 1)

    def peak_process_percent(self) -> float:
        """Return peak process CPU usage."""
        if not self._process_samples:
            return 0.0
        return max(self._process_samples)

    def peak_threads(self) -> int:
        """Return peak thread count observed."""
        if not self._thread_counts:
            return 0
        return max(self._thread_counts)

    def summary(self) -> dict[str, Any]:
        """Return a CPU usage summary."""
        return {
            "avg_system_percent": self.avg_system_percent(),
            "avg_process_percent": self.avg_process_percent(),
            "peak_process_percent": round(self.peak_process_percent(), 1),
            "peak_threads": self.peak_threads(),
            "snapshots_count": len(self._system_samples),
        }

    def reset(self) -> None:
        self._system_samples.clear()
        self._process_samples.clear()
        self._thread_counts.clear()
