"""
ArmPilot-AI — Recommendation Engine Tests
Tests for the rules-based recommendation engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.recommendation.engine import RecommendationEngine
from app.schemas.benchmark import BenchmarkConfig, BenchmarkResult, LatencyMetrics
from app.schemas.recommendation import Recommendation


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_result(
    *,
    status: str = "completed",
    memory_mb: float | None = None,
    model_size_mb: float | None = None,
    cpu_util: float | None = None,
    ttft_ms: float | None = None,
    tokens_per_second: float | None = None,
    p99_ms: float = 0.0,
    p95_ms: float = 0.0,
    p50_ms: float = 0.0,
    threads: int = 4,
    cpu_count_physical: int = 4,
) -> BenchmarkResult:
    """Helper to create a benchmark result with specific values."""
    config = BenchmarkConfig(model="test-model", threads=threads)
    latency = LatencyMetrics(p50_ms=p50_ms, p95_ms=p95_ms, p99_ms=p99_ms)
    return BenchmarkResult(
        id=f"bench-{uuid.uuid4().hex[:6]}",
        status=status,
        config=config,
        timestamp=datetime.now(timezone.utc).isoformat(),
        ttft_ms=ttft_ms,
        tokens_per_second=tokens_per_second,
        latency=latency,
        cpu_utilization_percent=cpu_util,
        memory_mb=memory_mb,
        model_size_mb=model_size_mb,
        hardware={"cpu_count_physical": cpu_count_physical, "cpu_count": cpu_count_physical},
    )


# ── Memory Rule Tests ─────────────────────────────────────────────────────────

class TestMemoryRecommendations:
    """Tests for memory-related recommendations."""

    def test_high_memory_triggers_warning(self):
        engine = RecommendationEngine()
        result = _make_result(memory_mb=5000.0)
        recs = engine._check_memory(result)
        assert len(recs) >= 1
        assert recs[0].severity == "warning"
        assert recs[0].category == "memory"
        assert "5000" in recs[0].problem

    def test_low_memory_no_warning(self):
        engine = RecommendationEngine()
        result = _make_result(memory_mb=2000.0)
        recs = engine._check_memory(result)
        assert len(recs) == 0

    def test_high_memory_ratio_triggers_info(self):
        engine = RecommendationEngine()
        result = _make_result(memory_mb=5000.0, model_size_mb=500.0)
        recs = engine._check_memory(result)
        # Should have both high memory and high ratio recommendations
        assert len(recs) >= 1

    def test_no_memory_data_no_recommendations(self):
        engine = RecommendationEngine()
        result = _make_result()
        recs = engine._check_memory(result)
        assert len(recs) == 0


# ── CPU Rule Tests ────────────────────────────────────────────────────────────

class TestCPURecommendations:
    """Tests for CPU-related recommendations."""

    def test_low_cpu_triggers_info(self):
        engine = RecommendationEngine()
        result = _make_result(cpu_util=30.0, cpu_count_physical=8)
        recs = engine._check_cpu(result)
        assert len(recs) >= 1
        assert any(r.category == "cpu" for r in recs)

    def test_high_cpu_triggers_warning(self):
        engine = RecommendationEngine()
        result = _make_result(cpu_util=96.0)
        recs = engine._check_cpu(result)
        assert len(recs) >= 1
        assert any(r.severity == "warning" for r in recs)

    def test_normal_cpu_no_recommendations(self):
        engine = RecommendationEngine()
        result = _make_result(cpu_util=60.0)
        recs = engine._check_cpu(result)
        assert len(recs) == 0

    def test_no_cpu_data_no_recommendations(self):
        engine = RecommendationEngine()
        result = _make_result()
        recs = engine._check_cpu(result)
        assert len(recs) == 0


# ── TTFT Rule Tests ──────────────────────────────────────────────────────────

class TestTTFTRecommendations:
    """Tests for TTFT-related recommendations."""

    def test_high_ttft_triggers_warning(self):
        engine = RecommendationEngine()
        result = _make_result(ttft_ms=600.0)
        recs = engine._check_ttft(result)
        assert len(recs) == 1
        assert recs[0].severity == "warning"

    def test_moderate_ttft_triggers_info(self):
        engine = RecommendationEngine()
        result = _make_result(ttft_ms=250.0)
        recs = engine._check_ttft(result)
        assert len(recs) == 1
        assert recs[0].severity == "info"

    def test_low_ttft_no_recommendations(self):
        engine = RecommendationEngine()
        result = _make_result(ttft_ms=50.0)
        recs = engine._check_ttft(result)
        assert len(recs) == 0

    def test_no_ttft_data_no_recommendations(self):
        engine = RecommendationEngine()
        result = _make_result()
        recs = engine._check_ttft(result)
        assert len(recs) == 0


# ── Throughput Rule Tests ─────────────────────────────────────────────────────

class TestThroughputRecommendations:
    """Tests for throughput-related recommendations."""

    def test_low_throughput_triggers_warning(self):
        engine = RecommendationEngine()
        result = _make_result(tokens_per_second=5.0)
        recs = engine._check_throughput(result)
        assert len(recs) == 1
        assert recs[0].category == "throughput"

    def test_good_throughput_no_recommendations(self):
        engine = RecommendationEngine()
        result = _make_result(tokens_per_second=20.0)
        recs = engine._check_throughput(result)
        assert len(recs) == 0


# ── Latency Rule Tests ───────────────────────────────────────────────────────

class TestLatencyRecommendations:
    """Tests for latency-related recommendations."""

    def test_high_p99_triggers_critical(self):
        engine = RecommendationEngine()
        result = _make_result(p99_ms=1500.0)
        recs = engine._check_latency(result)
        assert len(recs) >= 1
        assert any(r.severity == "critical" for r in recs)

    def test_high_variance_triggers_info(self):
        engine = RecommendationEngine()
        result = _make_result(p95_ms=600.0, p50_ms=100.0)
        recs = engine._check_latency(result)
        # p95/p50 ratio = 6.0, which is > 3
        assert any(r.category == "latency" for r in recs)

    def test_low_latency_no_recommendations(self):
        engine = RecommendationEngine()
        result = _make_result(p99_ms=200.0, p95_ms=150.0, p50_ms=100.0)
        recs = engine._check_latency(result)
        assert len(recs) == 0


# ── Thread Rule Tests ────────────────────────────────────────────────────────

class TestThreadRecommendations:
    """Tests for thread-related recommendations."""

    def test_over_subscribed_threads(self):
        engine = RecommendationEngine()
        result = _make_result(threads=16, cpu_count_physical=4)
        recs = engine._check_threads(result)
        assert len(recs) == 1
        assert recs[0].category == "configuration"
        assert "16" in recs[0].problem
        assert "4" in recs[0].recommendation

    def test_matching_threads_no_recommendation(self):
        engine = RecommendationEngine()
        result = _make_result(threads=4, cpu_count_physical=4)
        recs = engine._check_threads(result)
        assert len(recs) == 0

    def test_fewer_threads_no_recommendation(self):
        engine = RecommendationEngine()
        result = _make_result(threads=2, cpu_count_physical=8)
        recs = engine._check_threads(result)
        assert len(recs) == 0


# ── Full Analysis Tests ───────────────────────────────────────────────────────

class TestFullAnalysis:
    """Tests for the full analyze method."""

    def test_analyze_completed_result(self):
        engine = RecommendationEngine()
        result = _make_result(
            memory_mb=5000.0,
            cpu_util=30.0,
            ttft_ms=600.0,
            tokens_per_second=5.0,
            p99_ms=1500.0,
            threads=16,
            cpu_count_physical=4,
        )
        recs = engine.analyze(result)
        assert len(recs) > 0
        categories = {r.category for r in recs}
        assert "memory" in categories
        assert "cpu" in categories
        assert "latency" in categories

    def test_analyze_non_completed_returns_empty(self):
        engine = RecommendationEngine()
        result = _make_result(status="failed")
        recs = engine.analyze(result)
        assert len(recs) == 0

    def test_analyze_perfect_result_returns_empty(self):
        engine = RecommendationEngine()
        result = _make_result(
            memory_mb=1000.0,
            cpu_util=65.0,
            ttft_ms=30.0,
            tokens_per_second=50.0,
            p99_ms=200.0,
            p95_ms=150.0,
            p50_ms=100.0,
            threads=4,
            cpu_count_physical=4,
        )
        recs = engine.analyze(result)
        assert len(recs) == 0


# ── Recommendation Schema Tests ───────────────────────────────────────────────

class TestRecommendationSchema:
    """Tests for the Recommendation schema."""

    def test_recommendation_defaults(self):
        rec = Recommendation(
            id="rec-001",
            category="test",
            problem="problem",
            recommendation="fix",
            reason="reason",
            expected_goal="goal",
        )
        assert rec.severity == "info"
        assert rec.confidence == 0.5
        assert rec.suggested_config is None

    def test_recommendation_serialization(self):
        rec = Recommendation(
            id="rec-001",
            severity="warning",
            category="memory",
            problem="High usage",
            recommendation="Reduce",
            reason="Reason",
            expected_goal="Goal",
            suggested_config={"quantization": "INT8"},
            confidence=0.9,
        )
        data = rec.model_dump()
        assert data["severity"] == "warning"
        assert data["suggested_config"]["quantization"] == "INT8"
