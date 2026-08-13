"""
ArmPilot-AI — Benchmark Runner Tests
Tests for the benchmark runner: execution, metrics, percentiles.
"""

from __future__ import annotations

import statistics
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.benchmark.runner import BenchmarkRunner
from app.schemas.benchmark import BenchmarkConfig, BenchmarkResult, LatencyMetrics


# ── Percentile Calculation Tests ──────────────────────────────────────────────

class TestPercentileCalculation:
    """Tests for the static _percentile method."""

    def test_percentile_empty_list(self):
        assert BenchmarkRunner._percentile([], 50) == 0.0

    def test_percentile_single_element(self):
        assert BenchmarkRunner._percentile([100.0], 50) == 100.0

    def test_percentile_p50_even(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        result = BenchmarkRunner._percentile(data, 50)
        assert 5.0 <= result <= 6.0

    def test_percentile_p95(self):
        data = list(range(1, 101))
        result = BenchmarkRunner._percentile(data, 95)
        assert result >= 95

    def test_percentile_p99(self):
        data = list(range(1, 101))
        result = BenchmarkRunner._percentile(data, 99)
        assert result >= 99

    def test_percentile_p0(self):
        data = [10.0, 20.0, 30.0]
        result = BenchmarkRunner._percentile(data, 0)
        assert result == 10.0

    def test_percentile_p100(self):
        data = [10.0, 20.0, 30.0]
        result = BenchmarkRunner._percentile(data, 100)
        assert result == 30.0

    @pytest.mark.parametrize("p,expected_min,expected_max", [
        (50, 4.0, 6.0),
        (75, 7.0, 8.0),
        (90, 9.0, 10.0),
        (95, 9.0, 10.0),
        (25, 2.0, 4.0),
    ])
    def test_percentile_parametrized(self, p, expected_min, expected_max):
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        result = BenchmarkRunner._percentile(data, p)
        assert expected_min <= result <= expected_max


# ── Benchmark State Tests ─────────────────────────────────────────────────────

class TestBenchmarkState:
    """Tests for benchmark runner state management."""

    def test_initial_state(self):
        runner = BenchmarkRunner()
        assert runner.is_running is False
        assert runner._current_id is None


# ── Benchmark Execution Tests ─────────────────────────────────────────────────

class TestBenchmarkExecution:
    """Tests for benchmark execution flow."""

    @pytest.mark.asyncio
    @patch("app.benchmark.runner.get_process_metrics")
    @patch("app.benchmark.runner.get_system_metrics")
    @patch("app.benchmark.runner.get_hardware_info")
    @patch("app.benchmark.runner.inference_service")
    async def test_run_benchmark_success(
        self, mock_inference: MagicMock, mock_hw: MagicMock,
        mock_sys: MagicMock, mock_proc: MagicMock,
    ):
        mock_hw.return_value = {"architecture": "ARM64", "cpu_count": 4}
        mock_sys.return_value = {"cpu_utilization_percent": 50.0, "memory_used_mb": 2000.0}
        mock_proc.return_value = {"memory_rss_mb": 1500.0}

        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate_stream.return_value = iter([
            {"token": "Hello", "is_first": True, "is_last": False, "ttft_ms": 50.0},
            {"token": " World", "is_first": False, "is_last": True,
             "total_tokens": 2, "generation_time_ms": 200.0, "tokens_per_second": 10.0},
        ])
        mock_inference.runtime = mock_runtime

        runner = BenchmarkRunner()
        config = BenchmarkConfig(
            model="test-model",
            num_requests=2,
            warmup_requests=0,
            max_tokens=32,
        )
        result = await runner.run(config)

        assert result.status == "completed"
        assert result.total_requests == 2
        assert result.tokens_per_second > 0
        assert result.hardware is not None

    @pytest.mark.asyncio
    async def test_run_benchmark_already_running(self):
        runner = BenchmarkRunner()
        runner._running = True
        config = BenchmarkConfig(model="test-model")
        with pytest.raises(RuntimeError, match="already running"):
            await runner.run(config)

    @pytest.mark.asyncio
    @patch("app.benchmark.runner.get_process_metrics")
    @patch("app.benchmark.runner.get_system_metrics")
    @patch("app.benchmark.runner.get_hardware_info")
    @patch("app.benchmark.runner.inference_service")
    async def test_run_benchmark_with_warmup(
        self, mock_inference: MagicMock, mock_hw: MagicMock,
        mock_sys: MagicMock, mock_proc: MagicMock,
    ):
        mock_hw.return_value = {"architecture": "ARM64"}
        mock_sys.return_value = {"cpu_utilization_percent": 50.0}
        mock_proc.return_value = {}
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate_stream.return_value = iter([
            {"token": "x", "is_first": True, "is_last": True, "ttft_ms": 10.0,
             "total_tokens": 1, "generation_time_ms": 50.0, "tokens_per_second": 20.0},
        ])
        mock_inference.runtime = mock_runtime

        runner = BenchmarkRunner()
        config = BenchmarkConfig(
            model="test-model",
            num_requests=1,
            warmup_requests=2,
            max_tokens=16,
        )
        result = await runner.run(config)
        assert result.status == "completed"

    @pytest.mark.asyncio
    @patch("app.benchmark.runner.get_process_metrics")
    @patch("app.benchmark.runner.get_system_metrics")
    @patch("app.benchmark.runner.get_hardware_info")
    @patch("app.benchmark.runner.inference_service")
    async def test_run_benchmark_handles_request_failure(
        self, mock_inference: MagicMock, mock_hw: MagicMock,
        mock_sys: MagicMock, mock_proc: MagicMock,
    ):
        mock_hw.return_value = {"architecture": "ARM64"}
        mock_sys.return_value = {"cpu_utilization_percent": 50.0}
        mock_proc.return_value = {}
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate_stream.side_effect = [
            iter([{"token": "ok", "is_first": True, "is_last": True,
                   "ttft_ms": 10.0, "total_tokens": 1, "generation_time_ms": 50.0,
                   "tokens_per_second": 20.0}]),
            RuntimeError("Connection lost"),
        ]
        mock_inference.runtime = mock_runtime

        runner = BenchmarkRunner()
        config = BenchmarkConfig(model="test-model", num_requests=2, warmup_requests=0)
        result = await runner.run(config)
        assert result.status == "completed"
        assert result.total_requests == 1


# ── Benchmark Config Validation Tests ─────────────────────────────────────────

class TestBenchmarkConfig:
    """Tests for benchmark configuration validation."""

    def test_default_config(self):
        config = BenchmarkConfig(model="test-model")
        assert config.model == "test-model"
        assert config.batch_size == 512
        assert config.threads == 4
        assert config.concurrency == 1
        assert config.num_requests == 10

    @pytest.mark.parametrize("field,value", [
        ("batch_size", 0),
        ("threads", 0),
        ("concurrency", 0),
        ("num_requests", 0),
        ("max_tokens", 0),
        ("warmup_requests", -1),
    ])
    def test_config_rejects_invalid_values(self, field, value):
        with pytest.raises(Exception):
            BenchmarkConfig(model="test", **{field: value})

    def test_config_custom_values(self):
        config = BenchmarkConfig(
            model="custom",
            batch_size=256,
            threads=8,
            num_requests=50,
            max_tokens=512,
        )
        assert config.batch_size == 256
        assert config.threads == 8
        assert config.num_requests == 50


# ── Benchmark Result Tests ────────────────────────────────────────────────────

class TestBenchmarkResult:
    """Tests for benchmark result schema."""

    def test_result_default_values(self):
        result = BenchmarkResult(id="test", config=BenchmarkConfig(model="m"))
        assert result.status == "pending"
        assert result.ttft_ms is None
        assert result.tokens_per_second is None

    def test_result_with_latency(self):
        latency = LatencyMetrics(p50_ms=100, p95_ms=200, p99_ms=300)
        result = BenchmarkResult(
            id="test",
            config=BenchmarkConfig(model="m"),
            latency=latency,
        )
        assert result.latency.p50_ms == 100
        assert result.latency.p95_ms == 200

    def test_result_serialization(self):
        result = BenchmarkResult(
            id="bench-001",
            status="completed",
            config=BenchmarkConfig(model="test-model"),
            ttft_ms=50.0,
            tokens_per_second=15.0,
        )
        data = result.model_dump()
        assert data["id"] == "bench-001"
        assert data["status"] == "completed"
        assert data["ttft_ms"] == 50.0
