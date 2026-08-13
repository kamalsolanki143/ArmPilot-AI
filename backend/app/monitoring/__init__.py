"""
ArmPilot-AI — Monitoring Package
Provides metrics, telemetry, tracing, health monitoring, and profiling.
"""

from app.monitoring.metrics import (
    record_inference_request,
    record_inference_ttft,
    update_system_metrics,
    update_model_state,
    record_cache_hit,
    record_cache_miss,
    update_cache_size,
    get_metrics,
    get_content_type,
)
from app.monitoring.telemetry import TelemetryManager, telemetry_manager
from app.monitoring.tracing import (
    create_span,
    trace_operation,
    traced,
    TracingMiddleware,
)
from app.monitoring.health_monitor import (
    HealthStatus,
    HealthMonitor,
    health_monitor,
)
from app.monitoring.profiler import (
    ProfileResult,
    PerformanceProfiler,
    profiler,
    profile,
    profile_block,
    profile_inference,
)

__all__ = [
    # Metrics
    "record_inference_request",
    "record_inference_ttft",
    "update_system_metrics",
    "update_model_state",
    "record_cache_hit",
    "record_cache_miss",
    "update_cache_size",
    "get_metrics",
    "get_content_type",
    # Telemetry
    "TelemetryManager",
    "telemetry_manager",
    # Tracing
    "create_span",
    "trace_operation",
    "traced",
    "TracingMiddleware",
    # Health
    "HealthStatus",
    "HealthMonitor",
    "health_monitor",
    # Profiler
    "ProfileResult",
    "PerformanceProfiler",
    "profiler",
    "profile",
    "profile_block",
    "profile_inference",
]
