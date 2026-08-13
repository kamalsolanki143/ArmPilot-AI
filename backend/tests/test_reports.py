"""
ArmPilot-AI — Report Generation Tests
Tests for the markdown report builder.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.reports.report_builder import generate_benchmark_report, generate_optimization_report
from app.schemas.benchmark import BenchmarkConfig, BenchmarkResult, LatencyMetrics
from app.schemas.optimization import OptimizationCandidate, OptimizationConfig, OptimizationResult


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_benchmark_result(**kwargs) -> BenchmarkResult:
    """Create a benchmark result with sensible defaults."""
    defaults = dict(
        id=f"bench-{uuid.uuid4().hex[:6]}",
        status="completed",
        config=BenchmarkConfig(model="tiny-llama-1.1b", batch_size=512, threads=4,
                               num_requests=10, max_tokens=128),
        timestamp=datetime.now(timezone.utc).isoformat(),
        ttft_ms=85.3,
        tokens_per_second=12.5,
        requests_per_second=0.8,
        total_tokens=156,
        total_requests=10,
        latency=LatencyMetrics(p50_ms=1200, p75_ms=1400, p90_ms=1600,
                               p95_ms=1800, p99_ms=2200, avg_ms=1300,
                               min_ms=900, max_ms=2500),
        cpu_utilization_percent=65.0,
        memory_mb=1850.0,
        model_size_mb=637.0,
        duration_seconds=12.5,
        hardware={
            "architecture": "ARM64",
            "cpu_model": "Apple M1",
            "cpu_count": 8,
            "cpu_count_physical": 8,
            "memory_total_gb": 16.0,
            "is_arm64": True,
            "platform": "Darwin",
        },
    )
    defaults.update(kwargs)
    return BenchmarkResult(**defaults)


# ── Benchmark Report Tests ────────────────────────────────────────────────────

class TestBenchmarkReport:
    """Tests for benchmark markdown report generation."""

    def test_report_contains_title(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert "# ArmPilot-AI — Benchmark Report" in report

    def test_report_contains_id(self):
        result = _make_benchmark_result(id="bench-test123")
        report = generate_benchmark_report(result)
        assert "bench-test123" in report

    def test_report_contains_hardware_section(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert "## Hardware" in report
        assert "ARM64" in report

    def test_report_contains_configuration_section(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert "## Configuration" in report
        assert "tiny-llama-1.1b" in report

    def test_report_contains_results_section(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert "## Results" in report
        assert "12.5" in report  # tokens_per_second

    def test_report_contains_latency_section(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert "## Latency" in report
        assert "P95" in report
        assert "P99" in report

    def test_report_contains_resource_usage(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert "## Resource Usage" in report
        assert "1850.0" in report  # memory_mb

    def test_report_contains_reproduction(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert "## Reproduction" in report
        assert "arm-infer benchmark" in report

    def test_report_contains_timestamp(self):
        result = _make_benchmark_result(timestamp="2025-01-15T12:00:00Z")
        report = generate_benchmark_report(result)
        assert "2025-01-15T12:00:00Z" in report

    def test_report_handles_none_values(self):
        result = _make_benchmark_result(
            ttft_ms=None,
            tokens_per_second=None,
            cpu_utilization_percent=None,
            memory_mb=None,
            model_size_mb=None,
        )
        report = generate_benchmark_report(result)
        assert "N/A" in report

    def test_report_is_string(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert isinstance(report, str)

    def test_report_is_not_empty(self):
        result = _make_benchmark_result()
        report = generate_benchmark_report(result)
        assert len(report) > 200


# ── Optimization Report Tests ─────────────────────────────────────────────────

class TestOptimizationReport:
    """Tests for optimization markdown report generation."""

    def test_report_contains_title(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="test-model", objective="throughput"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        report = generate_optimization_report(result)
        assert "# ArmPilot-AI — Optimization Report" in report

    def test_report_contains_model(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="my-model"),
        )
        report = generate_optimization_report(result)
        assert "my-model" in report

    def test_report_contains_objective(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="m", objective="latency"),
        )
        report = generate_optimization_report(result)
        assert "latency" in report

    def test_report_with_baseline(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="m"),
            baseline={"tokens_per_second": 10.0, "ttft_ms": 120.0},
        )
        report = generate_optimization_report(result)
        assert "## Baseline" in report
        assert "10.0" in report

    def test_report_with_best_candidate(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="m"),
            best_candidate=OptimizationCandidate(
                id="cand-01",
                name="INT4 | batch=8 | threads=4",
                description="",
                tokens_per_second=18.5,
                ttft_ms=65.0,
                p95_latency_ms=900.0,
                memory_mb=1200.0,
            ),
        )
        report = generate_optimization_report(result)
        assert "## Best Configuration" in report
        assert "INT4" in report

    def test_report_with_improvements(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="m"),
            improvement_summary={
                "tokens_per_second": {"before": 10.0, "after": 18.5, "change_percent": 85.0},
            },
        )
        report = generate_optimization_report(result)
        assert "## Improvements" in report
        assert "+85.0%" in report

    def test_report_with_all_candidates(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="m"),
            candidates=[
                OptimizationCandidate(
                    id="c1", name="Config A", description="",
                    tokens_per_second=10.0, status="completed",
                ),
                OptimizationCandidate(
                    id="c2", name="Config B", description="",
                    tokens_per_second=15.0, status="completed",
                ),
            ],
        )
        report = generate_optimization_report(result)
        assert "## All Candidates" in report
        assert "Config A" in report
        assert "Config B" in report

    def test_report_empty_result(self):
        result = OptimizationResult(
            id="opt-test01",
            status="completed",
            config=OptimizationConfig(model="m"),
        )
        report = generate_optimization_report(result)
        assert "# ArmPilot-AI — Optimization Report" in report


# ── Format Helper Tests ───────────────────────────────────────────────────────

class TestFormatHelper:
    """Tests for the _fmt helper function."""

    def test_fmt_none(self):
        from app.reports.report_builder import _fmt
        assert _fmt(None) == "N/A"

    def test_fmt_float(self):
        from app.reports.report_builder import _fmt
        assert _fmt(12.5, "ms") == "12.5 ms"

    def test_fmt_int(self):
        from app.reports.report_builder import _fmt
        assert _fmt(42, "MB") == "42 MB"

    def test_fmt_float_no_unit(self):
        from app.reports.report_builder import _fmt
        assert _fmt(3.14) == "3.1"
