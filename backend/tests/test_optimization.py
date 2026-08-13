"""
ArmPilot-AI — Optimization Engine Tests
Tests for candidate generation, scoring, and optimization execution.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.optimization.optimizer import OptimizationEngine
from app.schemas.benchmark import BenchmarkConfig, BenchmarkResult, LatencyMetrics
from app.schemas.optimization import (
    OptimizationCandidate,
    OptimizationConfig,
    OptimizationResult,
)


# ── Candidate Generation Tests ────────────────────────────────────────────────

class TestCandidateGeneration:
    """Tests for optimization candidate generation."""

    def test_generate_candidates_basic(self):
        engine = OptimizationEngine()
        config = OptimizationConfig(
            model="test-model",
            quantization_options=["FP16", "INT4"],
            batch_sizes=[4, 8],
            thread_counts=[2, 4],
            max_candidates=10,
        )
        candidates = engine.generate_candidates(config)
        assert len(candidates) == 4  # 2 * 2 * 2 = 8, but limited by product

    def test_generate_candidates_respects_max(self):
        engine = OptimizationEngine()
        config = OptimizationConfig(
            model="test-model",
            quantization_options=["FP16", "INT8", "INT4"],
            batch_sizes=[1, 4, 8, 16],
            thread_counts=[2, 4, 8],
            max_candidates=5,
        )
        candidates = engine.generate_candidates(config)
        assert len(candidates) <= 5

    def test_generate_candidates_naming(self):
        engine = OptimizationEngine()
        config = OptimizationConfig(
            model="test-model",
            quantization_options=["INT8"],
            batch_sizes=[4],
            thread_counts=[2],
            max_candidates=10,
        )
        candidates = engine.generate_candidates(config)
        assert len(candidates) == 1
        assert "INT8" in candidates[0].name
        assert "batch=4" in candidates[0].name
        assert "threads=2" in candidates[0].name

    def test_generate_candidates_config_dict(self):
        engine = OptimizationEngine()
        config = OptimizationConfig(
            model="test-model",
            quantization_options=["INT4"],
            batch_sizes=[8],
            thread_counts=[4],
            max_candidates=10,
        )
        candidates = engine.generate_candidates(config)
        assert candidates[0].config["quantization"] == "INT4"
        assert candidates[0].config["batch_size"] == 8
        assert candidates[0].config["threads"] == 4
        assert candidates[0].config["model"] == "test-model"

    def test_generate_candidates_initial_status(self):
        engine = OptimizationEngine()
        config = OptimizationConfig(
            model="test-model",
            quantization_options=["FP16"],
            batch_sizes=[4],
            thread_counts=[2],
            max_candidates=10,
        )
        candidates = engine.generate_candidates(config)
        for c in candidates:
            assert c.status == "pending"


# ── Best Candidate Selection Tests ────────────────────────────────────────────

class TestSelectBest:
    """Tests for best candidate selection logic."""

    def _make_candidate(self, tps: float, ttft: float, mem: float, p95: float) -> OptimizationCandidate:
        return OptimizationCandidate(
            id=f"cand-{uuid.uuid4().hex[:6]}",
            name="test",
            description="",
            tokens_per_second=tps,
            ttft_ms=ttft,
            memory_mb=mem,
            p95_latency_ms=p95,
        )

    def test_select_best_throughput(self):
        engine = OptimizationEngine()
        candidates = [
            self._make_candidate(tps=10.0, ttft=100, mem=2000, p95=500),
            self._make_candidate(tps=20.0, ttft=80, mem=1500, p95=400),
            self._make_candidate(tps=15.0, ttft=90, mem=1800, p95=450),
        ]
        best = engine._select_best(candidates, "throughput")
        assert best.tokens_per_second == 20.0

    def test_select_best_latency(self):
        engine = OptimizationEngine()
        candidates = [
            self._make_candidate(tps=10.0, ttft=100, mem=2000, p95=500),
            self._make_candidate(tps=20.0, ttft=50, mem=1500, p95=300),
            self._make_candidate(tps=15.0, ttft=200, mem=1800, p95=800),
        ]
        best = engine._select_best(candidates, "latency")
        assert best.ttft_ms == 50

    def test_select_best_memory(self):
        engine = OptimizationEngine()
        candidates = [
            self._make_candidate(tps=10.0, ttft=100, mem=2000, p95=500),
            self._make_candidate(tps=20.0, ttft=50, mem=1000, p95=300),
            self._make_candidate(tps=15.0, ttft=200, mem=3000, p95=800),
        ]
        best = engine._select_best(candidates, "memory")
        assert best.memory_mb == 1000

    def test_select_best_balanced(self):
        engine = OptimizationEngine()
        candidates = [
            self._make_candidate(tps=10.0, ttft=100, mem=2000, p95=500),
            self._make_candidate(tps=20.0, ttft=50, mem=1500, p95=300),
        ]
        best = engine._select_best(candidates, "balanced")
        assert best is not None


# ── Balanced Score Tests ──────────────────────────────────────────────────────

class TestBalancedScore:
    """Tests for balanced optimization scoring."""

    def test_balanced_score_basic(self):
        c = OptimizationCandidate(
            id="c1", name="test", description="",
            tokens_per_second=15.0, ttft_ms=100, memory_mb=2000, p95_latency_ms=500,
        )
        score = OptimizationEngine._balanced_score(c)
        assert score > 0

    def test_balanced_score_higher_tps_is_better(self):
        c1 = OptimizationCandidate(
            id="c1", name="test", description="",
            tokens_per_second=10.0, ttft_ms=100, memory_mb=2000, p95_latency_ms=500,
        )
        c2 = OptimizationCandidate(
            id="c2", name="test", description="",
            tokens_per_second=20.0, ttft_ms=100, memory_mb=2000, p95_latency_ms=500,
        )
        assert OptimizationEngine._balanced_score(c2) > OptimizationEngine._balanced_score(c1)

    def test_balanced_score_lower_ttft_is_better(self):
        c1 = OptimizationCandidate(
            id="c1", name="test", description="",
            tokens_per_second=15.0, ttft_ms=200, memory_mb=2000, p95_latency_ms=500,
        )
        c2 = OptimizationCandidate(
            id="c2", name="test", description="",
            tokens_per_second=15.0, ttft_ms=50, memory_mb=2000, p95_latency_ms=500,
        )
        assert OptimizationEngine._balanced_score(c2) > OptimizationEngine._balanced_score(c1)

    def test_balanced_score_handles_zeroes(self):
        c = OptimizationCandidate(
            id="c1", name="test", description="",
            tokens_per_second=0, ttft_ms=0, memory_mb=0, p95_latency_ms=0,
        )
        score = OptimizationEngine._balanced_score(c)
        assert score == 0.0


# ── Improvement Computation Tests ─────────────────────────────────────────────

class TestComputeImprovements:
    """Tests for improvement percentage computation."""

    def test_compute_improvements_tps(self):
        baseline = {"tokens_per_second": 10.0}
        best = OptimizationCandidate(
            id="c1", name="test", description="",
            tokens_per_second=18.0,
        )
        result = OptimizationEngine._compute_improvements(baseline, best)
        assert result["tokens_per_second"]["change_percent"] == 80.0

    def test_compute_improvements_ttft(self):
        baseline = {"ttft_ms": 100.0}
        best = OptimizationCandidate(
            id="c1", name="test", description="",
            ttft_ms=60.0,
        )
        result = OptimizationEngine._compute_improvements(baseline, best)
        assert result["ttft_ms"]["change_percent"] == 40.0

    def test_compute_improvements_empty_baseline(self):
        best = OptimizationCandidate(
            id="c1", name="test", description="",
            tokens_per_second=10.0,
        )
        result = OptimizationEngine._compute_improvements({}, best)
        assert "tokens_per_second" not in result


# ── Optimization State Tests ──────────────────────────────────────────────────

class TestOptimizationState:
    """Tests for optimization engine state management."""

    def test_initial_state(self):
        engine = OptimizationEngine()
        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_already_running_raises(self):
        engine = OptimizationEngine()
        engine._running = True
        config = OptimizationConfig(model="test")
        with pytest.raises(RuntimeError, match="already running"):
            await engine.run(config)


# ── Optimization Config Validation Tests ──────────────────────────────────────

class TestOptimizationConfig:
    """Tests for optimization config validation."""

    def test_default_config(self):
        config = OptimizationConfig(model="test")
        assert config.objective == "throughput"
        assert config.max_candidates == 8
        assert "FP16" in config.quantization_options

    @pytest.mark.parametrize("objective", ["throughput", "latency", "memory", "balanced"])
    def test_valid_objectives(self, objective):
        config = OptimizationConfig(model="test", objective=objective)
        assert config.objective == objective

    def test_config_serialization(self):
        config = OptimizationConfig(
            model="test-model",
            objective="latency",
            batch_sizes=[4, 8, 16],
        )
        data = config.model_dump()
        assert data["model"] == "test-model"
        assert data["batch_sizes"] == [4, 8, 16]
