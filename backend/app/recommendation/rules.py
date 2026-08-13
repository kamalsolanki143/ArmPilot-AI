"""
ArmPilot-AI — Recommendation Rules
Defines rule conditions and actions for generating recommendations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.core.logger import logger
from app.schemas.benchmark import BenchmarkResult
from app.schemas.recommendation import Recommendation


@dataclass
class Rule:
    """A single recommendation rule."""
    name: str
    category: str
    description: str
    condition: Callable[[BenchmarkResult], bool]
    action: Callable[[BenchmarkResult], Recommendation]
    severity: str = "info"
    enabled: bool = True
    priority: int = 0


class RecommendationRules:
    """Registry of recommendation rules applied to benchmark results."""

    def __init__(self) -> None:
        self._rules: list[Rule] = []
        self._register_defaults()

    @property
    def rules(self) -> list[Rule]:
        return [r for r in self._rules if r.enabled]

    def register(self, rule: Rule) -> None:
        """Register a new rule."""
        self._rules.append(rule)
        logger.debug("Registered rule: %s", rule.name)

    def unregister(self, name: str) -> bool:
        """Unregister a rule by name."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def evaluate(self, result: BenchmarkResult) -> list[Recommendation]:
        """Evaluate all enabled rules against a benchmark result."""
        recommendations: list[Recommendation] = []

        sorted_rules = sorted(self.rules, key=lambda r: -r.priority)

        for rule in sorted_rules:
            try:
                if rule.condition(result):
                    rec = rule.action(result)
                    recommendations.append(rec)
                    logger.debug("Rule '%s' triggered: %s", rule.name, rec.problem)
            except Exception as e:
                logger.error("Rule '%s' failed: %s", rule.name, e)

        logger.info("Rules evaluation: %d recommendations generated", len(recommendations))
        return recommendations

    def _register_defaults(self) -> None:
        """Register built-in rules."""
        self.register(Rule(
            name="high_memory",
            category="memory",
            description="Detect high memory usage",
            severity="warning",
            priority=10,
            condition=lambda r: r.memory_mb is not None and r.memory_mb > 4000,
            action=self._rule_high_memory,
        ))

        self.register(Rule(
            name="low_cpu_utilization",
            category="cpu",
            description="Detect low CPU utilization",
            severity="info",
            priority=5,
            condition=lambda r: (
                r.cpu_utilization_percent is not None
                and r.cpu_utilization_percent < 40
            ),
            action=self._rule_low_cpu,
        ))

        self.register(Rule(
            name="high_cpu_saturation",
            category="cpu",
            description="Detect CPU saturation",
            severity="warning",
            priority=8,
            condition=lambda r: (
                r.cpu_utilization_percent is not None
                and r.cpu_utilization_percent > 95
            ),
            action=self._rule_high_cpu,
        ))

        self.register(Rule(
            name="high_ttft",
            category="latency",
            description="Detect high time-to-first-token",
            severity="warning",
            priority=9,
            condition=lambda r: r.ttft_ms is not None and r.ttft_ms > 200,
            action=self._rule_high_ttft,
        ))

        self.register(Rule(
            name="low_throughput",
            category="throughput",
            description="Detect low token throughput",
            severity="warning",
            priority=7,
            condition=lambda r: (
                r.tokens_per_second is not None
                and r.tokens_per_second < 10
            ),
            action=self._rule_low_throughput,
        ))

        self.register(Rule(
            name="high_p99_latency",
            category="latency",
            description="Detect high P99 latency",
            severity="critical",
            priority=10,
            condition=lambda r: r.latency.p99_ms > 1000,
            action=self._rule_high_p99,
        ))

        self.register(Rule(
            name="thread_over_subscription",
            category="configuration",
            description="Detect thread count exceeding physical cores",
            severity="info",
            priority=4,
            condition=self._cond_thread_over,
            action=self._rule_thread_over,
        ))

        self.register(Rule(
            name="memory_to_model_ratio",
            category="memory",
            description="Detect high runtime memory relative to model size",
            severity="info",
            priority=3,
            condition=self._cond_memory_ratio,
            action=self._rule_memory_ratio,
        ))

    def _rule_high_memory(self, r: BenchmarkResult) -> Recommendation:
        return Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity="warning",
            category="memory",
            problem=f"High memory consumption: {r.memory_mb:.0f} MB",
            recommendation="Test INT8 or INT4 quantization to reduce memory footprint",
            reason="Memory usage exceeds 4 GB, which may cause swapping on constrained Arm64 instances.",
            expected_goal="Reduce memory usage by 30-60% with quantization",
            suggested_config={"quantization": "INT8"},
            confidence=0.85,
        )

    def _rule_low_cpu(self, r: BenchmarkResult) -> Recommendation:
        hw = r.hardware or {}
        cpu_count = hw.get("cpu_count", 4)
        suggested = min(cpu_count, r.config.threads * 2)
        return Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity="info",
            category="cpu",
            problem=f"Low CPU utilization: {r.cpu_utilization_percent:.0f}%",
            recommendation=f"Increase thread count to {suggested} or raise concurrency",
            reason="CPU is underutilized; the inference pipeline is not fully leveraging available cores.",
            expected_goal="Increase CPU utilization to 60-80%",
            suggested_config={"threads": suggested, "concurrency": r.config.concurrency + 1},
            confidence=0.75,
        )

    def _rule_high_cpu(self, r: BenchmarkResult) -> Recommendation:
        return Recommendation(
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
        )

    def _rule_high_ttft(self, r: BenchmarkResult) -> Recommendation:
        severity = "warning" if r.ttft_ms > 500 else "info"
        return Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity=severity,
            category="latency",
            problem=f"High TTFT: {r.ttft_ms:.0f}ms",
            recommendation="Reduce context length, increase threads, or try INT4 quantization",
            reason="High TTFT directly impacts user-perceived responsiveness.",
            expected_goal="Reduce TTFT below 100ms",
            suggested_config={"threads": min(16, r.config.threads + 2), "quantization": "INT4"},
            confidence=0.8,
        )

    def _rule_low_throughput(self, r: BenchmarkResult) -> Recommendation:
        return Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity="warning",
            category="throughput",
            problem=f"Low throughput: {r.tokens_per_second:.1f} tokens/sec",
            recommendation="Test higher batch sizes and optimized thread configuration",
            reason="Throughput below 10 tokens/sec indicates significant optimization potential.",
            expected_goal="Achieve 20+ tokens/sec",
            suggested_config={
                "batch_size": r.config.batch_size * 2,
                "threads": min(16, r.config.threads + 2),
            },
            confidence=0.8,
        )

    def _rule_high_p99(self, r: BenchmarkResult) -> Recommendation:
        return Recommendation(
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
        )

    def _cond_thread_over(self, r: BenchmarkResult) -> bool:
        hw = r.hardware or {}
        physical_cores = hw.get("cpu_count_physical") or hw.get("cpu_count", 4)
        return r.config.threads > physical_cores

    def _rule_thread_over(self, r: BenchmarkResult) -> Recommendation:
        hw = r.hardware or {}
        physical_cores = hw.get("cpu_count_physical") or hw.get("cpu_count", 4)
        return Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity="info",
            category="configuration",
            problem=f"Thread count ({r.config.threads}) exceeds physical cores ({physical_cores})",
            recommendation=f"Set threads to {physical_cores} (physical core count)",
            reason="Over-subscribing threads beyond physical cores reduces performance due to context switching.",
            expected_goal="Match thread count to physical cores",
            suggested_config={"threads": physical_cores},
            confidence=0.75,
        )

    def _cond_memory_ratio(self, r: BenchmarkResult) -> bool:
        return (
            r.memory_mb is not None
            and r.model_size_mb is not None
            and r.model_size_mb > 0
            and (r.memory_mb / r.model_size_mb) > 3.0
        )

    def _rule_memory_ratio(self, r: BenchmarkResult) -> Recommendation:
        ratio = r.memory_mb / r.model_size_mb
        return Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity="info",
            category="memory",
            problem=f"Runtime memory ({r.memory_mb:.0f} MB) is {ratio:.1f}x model size ({r.model_size_mb:.0f} MB)",
            recommendation="Reduce KV-cache size or context length",
            reason="Large KV-cache allocations inflate memory well beyond model size.",
            expected_goal="Bring runtime memory closer to 2x model size",
            suggested_config={"kv_cache_size": "reduce", "context_length": 1024},
            confidence=0.7,
        )


# Singleton
recommendation_rules = RecommendationRules()
