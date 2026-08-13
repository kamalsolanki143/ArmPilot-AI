"""
ArmPilot-AI — Metrics Schemas
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class SystemMetrics(BaseModel):
    """Current system resource metrics."""
    cpu_utilization_percent: float = 0.0
    cpu_per_core_percent: list[float] = []
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    memory_total_mb: float = 0.0
    memory_used_percent: float = 0.0


class HardwareInfo(BaseModel):
    """Detected hardware information."""
    architecture: str = "Unknown"
    is_arm64: bool = False
    platform: str = "Unknown"
    platform_version: str = ""
    cpu_model: str = "Unknown"
    cpu_count: int = 1
    cpu_count_physical: Optional[int] = None
    cpu_freq_mhz: Optional[float] = None
    cpu_freq_max_mhz: Optional[float] = None
    memory_total_gb: float = 0.0
    memory_available_gb: float = 0.0
    memory_used_percent: float = 0.0
    python_version: str = ""


class MetricsResponse(BaseModel):
    """Combined metrics response for the dashboard."""
    hardware: HardwareInfo
    system: SystemMetrics
    inference: Optional[dict[str, Any]] = None
    timestamp: str = ""
