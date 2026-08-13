"""
ArmPilot-AI — Performance Analyzer
Analyzes benchmark results and identifies performance patterns.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.logger import logger
from app.schemas.benchmark import BenchmarkResult


class PerformanceAnalyzer:
    """Analyzes benchmark results to identify performance characteristics and patterns."""

    def analyze(self, result: BenchmarkResult) -> dict[str, Any]:
        """Perform a comprehensive analysis of a benchmark result."""
        if result.status != "completed":
            return {
                "status": result.status,
                "error": result.error,
                "analysis": {},
            }

        analysis: dict[str, Any] = {
            "throughput": self._analyze_throughput(result),
            "latency": self._analyze_latency(result),
            "memory": self._analyze_memory(result),
            "cpu": self._analyze_cpu(result),
            "bottleneck": self._identify_bottleneck(result),
            "grade": self._compute_grade(result),
        }

        logger.info(
            "Analysis complete for benchmark %s — grade=%s, bottleneck=%s",
            result.id, analysis["grade"], analysis["bottleneck"],
        )

        return analysis

    def compare(
        self,
        baseline: BenchmarkResult,
        optimized: BenchmarkResult,
    ) -> dict[str, Any]:
        """Compare two benchmark results and compute improvement deltas."""
        improvements: dict[str, Any] = {}

        # Throughput comparison
        if baseline.tokens_per_second and optimized.tokens_per_second:
            pct = self._percent_change(baseline.tokens_per_second, optimized.tokens_per_second)
            improvements["tokens_per_second"] = {
                "before": baseline.tokens_per_second,
                "after": optimized.tokens_per_second,
                "change_percent": round(pct, 2),
                "improved": pct > 0,
            }

        # TTFT comparison
        if baseline.ttft_ms and optimized.ttft_ms:
            pct = self._percent_change(baseline.ttft_ms, optimized.ttft_ms, invert=True)
            improvements["ttft_ms"] = {
                "before": baseline.ttft_ms,
                "after": optimized.ttft_ms,
                "change_percent": round(pct, 2),
                "improved": pct > 0,
            }

        # P95 latency
        if baseline.latency.p95_ms and optimized.latency.p95_ms:
            pct = self._percent_change(baseline.latency.p95_ms, optimized.latency.p95_ms, invert=True)
            improvements["p95_latency_ms"] = {
                "before": baseline.latency.p95_ms,
                "after": optimized.latency.p95_ms,
                "change_percent": round(pct, 2),
                "improved": pct > 0,
            }

        # Memory
        if baseline.memory_mb and optimized.memory_mb:
            pct = self._percent_change(baseline.memory_mb, optimized.memory_mb, invert=True)
            improvements["memory_mb"] = {
                "before": baseline.memory_mb,
                "after": optimized.memory_mb,
                "change_percent": round(pct, 2),
                "improved": pct > 0,
            }

        return {
            "baseline_id": baseline.id,
            "optimized_id": optimized.id,
            "improvements": improvements,
            "overall_improved": sum(
                1 for v in improvements.values() if v.get("improved", False)
            ) > len(improvements) / 2,
        }

    def _analyze_throughput(self, r: BenchmarkResult) -> dict[str, Any]:
        """Analyze throughput characteristics."""
        tps = r.tokens_per_second or 0
        rps = r.requests_per_second or 0

        rating = "excellent"
        if tps < 10:
            rating = "poor"
        elif tps < 20:
            rating = "below_average"
        elif tps < 30:
            rating = "average"
        elif tps < 50:
            rating = "good"

        return {
            "tokens_per_second": tps,
            "requests_per_second": rps,
            "total_tokens": r.total_tokens,
            "rating": rating,
        }

    def _analyze_latency(self, r: BenchmarkResult) -> dict[str, Any]:
        """Analyze latency characteristics."""
        lat = r.latency

        # Compute variance indicator
        variance_ratio = lat.p95_ms / lat.p50_ms if lat.p50_ms > 0 else 0

        rating = "excellent"
        if lat.p95_ms > 500:
            rating = "poor"
        elif lat.p95_ms > 200:
            rating = "below_average"
        elif lat.p95_ms > 100:
            rating = "average"
        elif lat.p95_ms > 50:
            rating = "good"

        return {
            "ttft_ms": r.ttft_ms,
            "p50_ms": lat.p50_ms,
            "p95_ms": lat.p95_ms,
            "p99_ms": lat.p99_ms,
            "avg_ms": lat.avg_ms,
            "variance_ratio": round(variance_ratio, 2),
            "high_variance": variance_ratio > 3.0,
            "rating": rating,
        }

    def _analyze_memory(self, r: BenchmarkResult) -> dict[str, Any]:
        """Analyze memory usage."""
        memory_mb = r.memory_mb or 0
        model_size_mb = r.model_size_mb or 0
        overhead_ratio = memory_mb / model_size_mb if model_size_mb > 0 else 0

        rating = "excellent"
        if overhead_ratio > 4:
            rating = "poor"
        elif overhead_ratio > 3:
            rating = "below_average"
        elif overhead_ratio > 2.5:
            rating = "average"
        elif overhead_ratio > 2:
            rating = "good"

        return {
            "memory_mb": memory_mb,
            "model_size_mb": model_size_mb,
            "overhead_ratio": round(overhead_ratio, 2),
            "rating": rating,
        }

    def _analyze_cpu(self, r: BenchmarkResult) -> dict[str, Any]:
        """Analyze CPU utilization."""
        cpu = r.cpu_utilization_percent or 0
        hw = r.hardware or {}
        thread_count = r.config.threads
        physical_cores = hw.get("cpu_count_physical") or hw.get("cpu_count", 4)

        thread_efficiency = "optimal"
        if thread_count > physical_cores:
            thread_efficiency = "oversubscribed"
        elif thread_count < physical_cores * 0.5:
            thread_efficiency = "underutilized"

        rating = "excellent"
        if cpu > 95:
            rating = "saturated"
        elif cpu > 80:
            rating = "good"
        elif cpu > 50:
            rating = "moderate"
        elif cpu > 0:
            rating = "low"

        return {
            "utilization_percent": cpu,
            "thread_count": thread_count,
            "physical_cores": physical_cores,
            "thread_efficiency": thread_efficiency,
            "rating": rating,
        }

    def _identify_bottleneck(self, r: BenchmarkResult) -> str:
        """Identify the primary performance bottleneck."""
        bottlenecks: list[tuple[str, float]] = []

        if r.cpu_utilization_percent and r.cpu_utilization_percent > 90:
            bottlenecks.append(("cpu_saturated", r.cpu_utilization_percent))

        if r.ttft_ms and r.ttft_ms > 200:
            bottlenecks.append(("high_ttft", r.ttft_ms))

        if r.tokens_per_second and r.tokens_per_second < 10:
            bottlenecks.append(("low_throughput", 100 - r.tokens_per_second))

        if r.memory_mb and r.memory_mb > 4000:
            bottlenecks.append(("high_memory", r.memory_mb))

        if r.latency.p99_ms > 1000:
            bottlenecks.append(("high_tail_latency", r.latency.p99_ms))

        if not bottlenecks:
            return "none"

        bottlenecks.sort(key=lambda x: x[1], reverse=True)
        return bottlenecks[0][0]

    def _compute_grade(self, r: BenchmarkResult) -> str:
        """Compute an overall performance grade from A+ to F."""
        score = 100

        # Throughput scoring
        tps = r.tokens_per_second or 0
        if tps < 10:
            score -= 30
        elif tps < 20:
            score -= 15
        elif tps < 30:
            score -= 5
        elif tps > 50:
            score += 5

        # Latency scoring
        if r.latency.p95_ms > 500:
            score -= 25
        elif r.latency.p95_ms > 200:
            score -= 10
        elif r.latency.p95_ms < 50:
            score += 5

        if r.ttft_ms and r.ttft_ms > 300:
            score -= 15
        elif r.ttft_ms and r.ttft_ms < 100:
            score += 5

        # Memory scoring
        if r.memory_mb and r.memory_mb > 6000:
            score -= 15
        elif r.memory_mb and r.memory_mb > 4000:
            score -= 5

        # CPU scoring
        if r.cpu_utilization_percent and r.cpu_utilization_percent > 95:
            score -= 10

        # Map score to grade
        if score >= 95:
            return "A+"
        if score >= 90:
            return "A"
        if score >= 85:
            return "A-"
        if score >= 80:
            return "B+"
        if score >= 75:
            return "B"
        if score >= 70:
            return "B-"
        if score >= 65:
            return "C+"
        if score >= 60:
            return "C"
        if score >= 55:
            return "C-"
        if score >= 50:
            return "D"
        return "F"

    @staticmethod
    def _percent_change(
        before: float,
        after: float,
        invert: bool = False,
    ) -> float:
        """Compute percentage change. Invert=True for metrics where lower is better."""
        if before == 0:
            return 0.0
        pct = ((after - before) / before) * 100
        return -pct if invert else pct


# Singleton
performance_analyzer = PerformanceAnalyzer()
