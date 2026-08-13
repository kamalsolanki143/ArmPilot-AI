"""
ArmPilot-AI — Recommendation Rules Engine
Rules-based analysis of benchmark results with actionable recommendations.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.core.logger import logger
from app.schemas.benchmark import BenchmarkResult
from app.schemas.recommendation import Recommendation


class RecommendationEngine:
    """Generates optimization recommendations based on benchmark results."""

    def analyze(self, result: BenchmarkResult) -> list[Recommendation]:
        """Analyze a benchmark result and generate recommendations."""
        recommendations: list[Recommendation] = []

        if result.status != "completed":
            return recommendations

        # Run all rule checks
        recommendations.extend(self._check_memory(result))
        recommendations.extend(self._check_cpu(result))
        recommendations.extend(self._check_ttft(result))
        recommendations.extend(self._check_throughput(result))
        recommendations.extend(self._check_latency(result))
        recommendations.extend(self._check_threads(result))

        logger.info("Generated %d recommendations for benchmark %s",
                     len(recommendations), result.id)
        return recommendations

    def _check_memory(self, r: BenchmarkResult) -> list[Recommendation]:
        """Check for high memory usage."""
        recs: list[Recommendation] = []

        if r.memory_mb and r.memory_mb > 4000:
            recs.append(Recommendation(
                id=f"rec-{uuid.uuid4().hex[:6]}",
                severity="warning",
                category="memory",
                problem=f"High memory consumption: {r.memory_mb:.0f} MB",
                recommendation="Test INT8 or INT4 quantization to reduce memory footprint",
                reason=(
                    "Memory usage exceeds 4 GB, which may cause swapping on constrained "
                    "Arm64 instances and degrade performance."
                ),
                expected_goal="Reduce memory usage by 30-60% with quantization",
                suggested_config={
                    "quantization": "INT8",
                    "action": "Reduce model precision",
                },
                confidence=0.85,
            ))

        if r.memory_mb and r.model_size_mb:
            ratio = r.memory_mb / r.model_size_mb
            if ratio > 3.0:
                recs.append(Recommendation(
                    id=f"rec-{uuid.uuid4().hex[:6]}",
                    severity="info",
                    category="memory",
                    problem=f"Runtime memory ({r.memory_mb:.0f} MB) is {ratio:.1f}x model size ({r.model_size_mb:.0f} MB)",
                    recommendation="Reduce KV-cache size or context length",
                    reason="Large KV-cache allocations can inflate memory well beyond model size.",
                    expected_goal="Bring runtime memory closer to 2x model size",
                    suggested_config={
                        "kv_cache_size": "reduce",
                        "context_length": 1024,
                    },
                    confidence=0.7,
                ))

        return recs

    def _check_cpu(self, r: BenchmarkResult) -> list[Recommendation]:
        """Check for CPU utilization issues."""
        recs: list[Recommendation] = []

        if r.cpu_utilization_percent is not None and r.cpu_utilization_percent < 40:
            hw = r.hardware or {}
            cpu_count = hw.get("cpu_count", 4)
            suggested_threads = min(cpu_count, r.config.threads * 2)

            recs.append(Recommendation(
                id=f"rec-{uuid.uuid4().hex[:6]}",
                severity="info",
                category="cpu",
                problem=f"Low CPU utilization: {r.cpu_utilization_percent:.0f}%",
                recommendation=f"Increase thread count to {suggested_threads} or raise concurrency",
                reason=(
                    "CPU is underutilized, indicating the inference pipeline is not "
                    "fully leveraging available compute cores."
                ),
                expected_goal="Increase CPU utilization to 60-80% for better throughput",
                suggested_config={
                    "threads": suggested_threads,
                    "concurrency": r.config.concurrency + 1,
                },
                confidence=0.75,
            ))

        if r.cpu_utilization_percent is not None and r.cpu_utilization_percent > 95:
            recs.append(Recommendation(
                id=f"rec-{uuid.uuid4().hex[:6]}",
                severity="warning",
                category="cpu",
                problem=f"CPU saturation: {r.cpu_utilization_percent:.0f}%",
                recommendation="Reduce concurrency or batch size to prevent thermal throttling",
                reason="Sustained 95%+ CPU may cause thermal throttling on Arm SoCs.",
                expected_goal="Reduce CPU to 80-90% for sustained performance",
                suggested_config={
                    "concurrency": max(1, r.config.concurrency - 1),
                    "batch_size": max(1, r.config.batch_size // 2),
                },
                confidence=0.7,
            ))

        return recs

    def _check_ttft(self, r: BenchmarkResult) -> list[Recommendation]:
        """Check Time To First Token."""
        recs: list[Recommendation] = []

        if r.ttft_ms and r.ttft_ms > 200:
            recs.append(Recommendation(
                id=f"rec-{uuid.uuid4().hex[:6]}",
                severity="warning" if r.ttft_ms > 500 else "info",
                category="latency",
                problem=f"High TTFT: {r.ttft_ms:.0f}ms",
                recommendation="Reduce context length, increase threads, or try INT4 quantization",
                reason=(
                    "Time to first token is high. This directly impacts user-perceived "
                    "responsiveness in interactive applications."
                ),
                expected_goal="Reduce TTFT below 100ms for responsive interaction",
                suggested_config={
                    "threads": min(16, r.config.threads + 2),
                    "quantization": "INT4",
                    "context_length": min(r.config.batch_size, 1024),
                },
                confidence=0.8,
            ))

        return recs

    def _check_throughput(self, r: BenchmarkResult) -> list[Recommendation]:
        """Check token throughput."""
        recs: list[Recommendation] = []

        if r.tokens_per_second is not None and r.tokens_per_second < 10:
            recs.append(Recommendation(
                id=f"rec-{uuid.uuid4().hex[:6]}",
                severity="warning",
                category="throughput",
                problem=f"Low throughput: {r.tokens_per_second:.1f} tokens/sec",
                recommendation="Test higher batch sizes and optimized thread configuration",
                reason="Throughput below 10 tokens/sec indicates significant optimization potential.",
                expected_goal="Achieve 20+ tokens/sec through batch and thread tuning",
                suggested_config={
                    "batch_size": r.config.batch_size * 2,
                    "threads": min(16, r.config.threads + 2),
                },
                confidence=0.8,
            ))

        return recs

    def _check_latency(self, r: BenchmarkResult) -> list[Recommendation]:
        """Check P95/P99 latency."""
        recs: list[Recommendation] = []

        if r.latency.p99_ms > 1000:
            recs.append(Recommendation(
                id=f"rec-{uuid.uuid4().hex[:6]}",
                severity="critical",
                category="latency",
                problem=f"P99 latency exceeds 1 second: {r.latency.p99_ms:.0f}ms",
                recommendation="Reduce concurrency and batch size, or use a smaller model",
                reason="High tail latency indicates resource contention or model overload.",
                expected_goal="Bring P99 latency below 500ms",
                suggested_config={
                    "concurrency": max(1, r.config.concurrency - 1),
                    "batch_size": max(1, r.config.batch_size // 2),
                },
                confidence=0.85,
            ))

        if r.latency.p95_ms > 0 and r.latency.p50_ms > 0:
            ratio = r.latency.p95_ms / r.latency.p50_ms
            if ratio > 3:
                recs.append(Recommendation(
                    id=f"rec-{uuid.uuid4().hex[:6]}",
                    severity="info",
                    category="latency",
                    problem=f"High latency variance: P95/P50 ratio = {ratio:.1f}x",
                    recommendation="Investigate resource contention; consider CPU affinity pinning",
                    reason="High variance between median and tail latency suggests external interference.",
                    expected_goal="Reduce P95/P50 ratio below 2x for predictable performance",
                    suggested_config={
                        "cpu_affinity": "pin_to_cores",
                    },
                    confidence=0.6,
                ))

        return recs

    def _check_threads(self, r: BenchmarkResult) -> list[Recommendation]:
        """Check thread configuration relative to hardware."""
        recs: list[Recommendation] = []

        hw = r.hardware or {}
        physical_cores = hw.get("cpu_count_physical") or hw.get("cpu_count", 4)

        if r.config.threads > physical_cores:
            recs.append(Recommendation(
                id=f"rec-{uuid.uuid4().hex[:6]}",
                severity="info",
                category="configuration",
                problem=f"Thread count ({r.config.threads}) exceeds physical cores ({physical_cores})",
                recommendation=f"Set threads to {physical_cores} (physical core count)",
                reason="Over-subscribing threads beyond physical cores can reduce performance due to context switching.",
                expected_goal="Match thread count to physical cores for optimal throughput",
                suggested_config={
                    "threads": physical_cores,
                },
                confidence=0.75,
            ))

        return recs


# Singleton
recommendation_engine = RecommendationEngine()
