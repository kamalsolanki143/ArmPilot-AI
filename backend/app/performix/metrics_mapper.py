"""
ArmPilot-AI — PerformiX Metrics Mapper
Maps parsed PerformiX metrics to ArmPilot's internal format.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.logger import logger
from app.schemas.benchmark import BenchmarkResult, LatencyMetrics


# Mapping from PerformiX metric names to ArmPilot internal names
_METRIC_MAP: dict[str, str] = {
    "throughput": "tokens_per_second",
    "tokens_per_sec": "tokens_per_second",
    "tps": "tokens_per_second",
    "tok_per_sec": "tokens_per_second",
    "latency": "avg_latency_ms",
    "avg_latency": "avg_latency_ms",
    "avg_latency_ms": "avg_latency_ms",
    "p50": "p50_ms",
    "p50_latency": "p50_ms",
    "p50_ms": "p50_ms",
    "p95": "p95_ms",
    "p95_latency": "p95_ms",
    "p95_ms": "p95_ms",
    "p99": "p99_ms",
    "p99_latency": "p99_ms",
    "p99_ms": "p99_ms",
    "ttft": "ttft_ms",
    "time_to_first_token": "ttft_ms",
    "first_token_latency": "ttft_ms",
    "memory_usage": "memory_mb",
    "memory_mb": "memory_mb",
    "ram_usage": "memory_mb",
    "cpu_usage": "cpu_utilization_percent",
    "cpu_utilization": "cpu_utilization_percent",
    "cpu_percent": "cpu_utilization_percent",
    "model_size": "model_size_mb",
    "model_size_mb": "model_size_mb",
}

# Mapping from category+metric to internal metric name
_CATEGORY_METRIC_MAP: dict[str, dict[str, str]] = {
    "latency": {
        "p50": "p50_ms",
        "p75": "p75_ms",
        "p90": "p90_ms",
        "p95": "p95_ms",
        "p99": "p99_ms",
        "avg": "avg_latency_ms",
        "min": "min_ms",
        "max": "max_ms",
        "mean": "avg_latency_ms",
    },
    "throughput": {
        "tokens_per_second": "tokens_per_second",
        "tps": "tokens_per_second",
        "requests_per_second": "requests_per_second",
    },
    "memory": {
        "usage": "memory_mb",
        "peak": "memory_peak_mb",
        "used": "memory_mb",
    },
    "cpu": {
        "utilization": "cpu_utilization_percent",
        "usage": "cpu_utilization_percent",
    },
}


class PerformixMetricsMapper:
    """Maps PerformiX parsed output to ArmPilot internal benchmark metrics."""

    def __init__(self) -> None:
        self._custom_mappings: dict[str, str] = {}

    def add_mapping(self, performix_name: str, internal_name: str) -> None:
        """Add a custom metric mapping."""
        self._custom_mappings[performix_name.lower()] = internal_name

    def map_to_benchmark_result(
        self,
        parsed_metrics: dict[str, Any],
        summary: Optional[dict[str, Any]] = None,
        model: str = "unknown",
    ) -> dict[str, Any]:
        """Map parsed PerformiX metrics to a dict compatible with BenchmarkResult fields."""
        result: dict[str, Any] = {
            "model": model,
            "source": "performix",
        }

        # Flatten and map metrics from sections
        flat_metrics = self._flatten_metrics(parsed_metrics)

        for key, data in flat_metrics.items():
            internal_name = self._resolve_mapping(key)
            if internal_name and isinstance(data, dict):
                result[internal_name] = data.get("value", data)

        # Map summary metrics
        if summary:
            for key, value in summary.items():
                internal_name = self._resolve_mapping(key)
                if internal_name:
                    result[internal_name] = value

        # Build latency object
        latency = LatencyMetrics()
        for field in ["p50_ms", "p75_ms", "p90_ms", "p95_ms", "p99_ms", "avg_ms", "min_ms", "max_ms"]:
            if field in result:
                setattr(latency, field, float(result.pop(field)))
        if latency.avg_ms == 0 and "avg_latency_ms" in result:
            latency.avg_ms = float(result.pop("avg_latency_ms"))
        result["latency"] = latency

        logger.info(
            "Mapped PerformiX metrics: %d fields mapped",
            sum(1 for k in result if k != "source"),
        )

        return result

    def map_to_internal(self, parsed_metrics: dict[str, Any]) -> dict[str, Any]:
        """Map parsed metrics to internal format without building a full result."""
        flat = self._flatten_metrics(parsed_metrics)
        mapped: dict[str, Any] = {}

        for key, data in flat.items():
            internal_name = self._resolve_mapping(key)
            if internal_name and isinstance(data, dict):
                mapped[internal_name] = data.get("value", data)

        return mapped

    def _flatten_metrics(self, parsed_metrics: dict[str, Any]) -> dict[str, Any]:
        """Flatten nested section:metric structure."""
        flat: dict[str, Any] = {}

        for section, metrics in parsed_metrics.items():
            if not isinstance(metrics, dict):
                continue
            for metric_name, data in metrics.items():
                flat[metric_name] = data
                # Also store with category prefix for disambiguation
                flat[f"{section}.{metric_name}"] = data

        return flat

    def _resolve_mapping(self, name: str) -> Optional[str]:
        """Resolve a PerformiX metric name to an internal name."""
        lower = name.lower().strip()

        # Check custom mappings first
        if lower in self._custom_mappings:
            return self._custom_mappings[lower]

        # Check global metric map
        if lower in _METRIC_MAP:
            return _METRIC_MAP[lower]

        # Check category.metric map
        if "." in lower:
            category, _, metric = lower.partition(".")
            if category in _CATEGORY_METRIC_MAP:
                return _CATEGORY_METRIC_MAP[category].get(metric)

        return None


# Singleton
performix_metrics_mapper = PerformixMetricsMapper()
