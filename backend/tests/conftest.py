"""
ArmPilot-AI — Shared Test Fixtures
pytest fixtures for all test modules.
"""

from __future__ import annotations

import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.models.user import User, UserRole
from app.schemas.auth import TokenPair, UserRegister
from app.schemas.benchmark import BenchmarkConfig, BenchmarkResult, LatencyMetrics
from app.schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    ModelInfo,
    UsageInfo,
)
from app.schemas.optimization import OptimizationCandidate, OptimizationConfig, OptimizationResult
from app.schemas.recommendation import Recommendation
from app.schemas.reports import ReportResponse


# ── Temporary Directory Fixture ────────────────────────────────────────────────

@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "users").mkdir()
    (data_dir / "benchmarks").mkdir()
    (data_dir / "optimizations").mkdir()
    (data_dir / "reports").mkdir()
    return data_dir


# ── Settings Fixture ──────────────────────────────────────────────────────────

@pytest.fixture
def test_settings(tmp_data_dir: Path) -> Generator[Settings, None, None]:
    """Provide test settings with temporary directories."""
    with patch.object(settings, "base_dir", tmp_data_dir), \
         patch.object(settings, "data_dir", tmp_data_dir / "data"), \
         patch.object(settings, "debug", True), \
         patch.object(settings, "jwt_secret_key", "test-secret-key-for-testing"):
        yield settings


# ── User Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    return User(
        id="test-user-001",
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$LJ3m4ys4Gz8nMfH3uIuOaOqX1aZbVcNnMmLkKjJhGfDnOvCbYaXi",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def admin_user() -> User:
    """Create an admin user for testing."""
    return User(
        id="admin-user-001",
        email="admin@example.com",
        username="admin",
        hashed_password="$2b$12$LJ3m4ys4Gz8nMfH3uIuOaOqX1aZbVcNnMmLkKjJhGfDnOvCbYaXi",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def inactive_user() -> User:
    """Create an inactive user for testing."""
    return User(
        id="inactive-user-001",
        email="inactive@example.com",
        username="inactive",
        hashed_password="$2b$12$LJ3m4ys4Gz8nMfH3uIuOaOqX1aZbVcNnMmLkKjJhGfDnOvCbYaXi",
        full_name="Inactive User",
        role=UserRole.USER,
        is_active=False,
        is_verified=False,
    )


@pytest.fixture
def user_register_data() -> UserRegister:
    """Sample user registration data."""
    return UserRegister(
        email="newuser@example.com",
        username="newuser",
        password="securepass123",
        full_name="New User",
    )


# ── Token Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_token_pair() -> TokenPair:
    """Create a sample token pair."""
    return TokenPair(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.access",
        refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.refresh",
        token_type="bearer",
        expires_in=3600,
    )


# ── Model Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_model_info() -> ModelInfo:
    """Create sample model info."""
    return ModelInfo(
        id="tiny-llama-1.1b",
        name="TinyLlama 1.1B",
        parameters="1.1B",
        quantization="Q4_K_M",
        size_mb=637.0,
        context_length=2048,
        runtime="llama.cpp",
        file_path="/models/tinyllama-1.1b-q4_k_m.gguf",
        loaded=False,
    )


@pytest.fixture
def loaded_model_info() -> ModelInfo:
    """Create model info for a loaded model."""
    return ModelInfo(
        id="tiny-llama-1.1b",
        name="TinyLlama 1.1B",
        parameters="1.1B",
        quantization="Q4_K_M",
        size_mb=637.0,
        context_length=2048,
        runtime="llama.cpp",
        file_path="/models/tinyllama-1.1b-q4_k_m.gguf",
        loaded=True,
    )


# ── Inference Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def sample_chat_message() -> ChatMessage:
    """Create a sample chat message."""
    return ChatMessage(role="user", content="What is ARM64 architecture?")


@pytest.fixture
def sample_chat_request() -> ChatCompletionRequest:
    """Create a sample chat completion request."""
    return ChatCompletionRequest(
        model="tiny-llama-1.1b",
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="What is ARM64 architecture?"),
        ],
        temperature=0.7,
        max_tokens=128,
    )


@pytest.fixture
def sample_chat_response() -> ChatCompletionResponse:
    """Create a sample chat completion response."""
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(datetime.now(timezone.utc).timestamp()),
        model="tiny-llama-1.1b",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="ARM64 is a 64-bit processor architecture."),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(prompt_tokens=12, completion_tokens=10, total_tokens=22),
    )


# ── Benchmark Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def sample_benchmark_config() -> BenchmarkConfig:
    """Create a sample benchmark configuration."""
    return BenchmarkConfig(
        model="tiny-llama-1.1b",
        runtime="llama.cpp",
        batch_size=512,
        threads=4,
        concurrency=1,
        num_requests=10,
        max_tokens=128,
        warmup_requests=2,
        prompt="Explain the benefits of ARM64 architecture.",
    )


@pytest.fixture
def sample_benchmark_result() -> BenchmarkResult:
    """Create a sample completed benchmark result."""
    return BenchmarkResult(
        id="bench-test001",
        status="completed",
        config=BenchmarkConfig(
            model="tiny-llama-1.1b",
            batch_size=512,
            threads=4,
            num_requests=10,
            max_tokens=128,
        ),
        timestamp=datetime.now(timezone.utc).isoformat(),
        ttft_ms=85.3,
        tokens_per_second=12.5,
        requests_per_second=0.8,
        total_tokens=156,
        total_requests=10,
        latency=LatencyMetrics(
            p50_ms=1200.0,
            p75_ms=1400.0,
            p90_ms=1600.0,
            p95_ms=1800.0,
            p99_ms=2200.0,
            avg_ms=1300.0,
            min_ms=900.0,
            max_ms=2500.0,
        ),
        cpu_utilization_percent=65.0,
        memory_mb=1850.0,
        memory_peak_mb=2100.0,
        model_size_mb=637.0,
        duration_seconds=12.5,
        hardware={
            "architecture": "ARM64",
            "is_arm64": True,
            "cpu_model": "Apple M1",
            "cpu_count": 8,
            "cpu_count_physical": 8,
            "memory_total_gb": 16.0,
        },
    )


@pytest.fixture
def high_memory_benchmark_result() -> BenchmarkResult:
    """Benchmark result with high memory usage."""
    return BenchmarkResult(
        id="bench-high-mem",
        status="completed",
        config=BenchmarkConfig(model="tiny-llama-1.1b", batch_size=512, threads=4,
                               num_requests=10, max_tokens=128),
        timestamp=datetime.now(timezone.utc).isoformat(),
        ttft_ms=85.3,
        tokens_per_second=12.5,
        total_tokens=156,
        total_requests=10,
        latency=LatencyMetrics(p50_ms=1200, p95_ms=1800, p99_ms=2200),
        memory_mb=5000.0,
        model_size_mb=800.0,
        hardware={"architecture": "ARM64", "is_arm64": True},
    )


@pytest.fixture
def low_throughput_benchmark_result() -> BenchmarkResult:
    """Benchmark result with low throughput."""
    return BenchmarkResult(
        id="bench-low-tps",
        status="completed",
        config=BenchmarkConfig(model="tiny-llama-1.1b", batch_size=512, threads=4,
                               num_requests=10, max_tokens=128),
        timestamp=datetime.now(timezone.utc).isoformat(),
        ttft_ms=85.3,
        tokens_per_second=5.0,
        total_tokens=156,
        total_requests=10,
        latency=LatencyMetrics(p50_ms=1200, p95_ms=1800, p99_ms=2200),
        memory_mb=1850.0,
        model_size_mb=637.0,
        hardware={"architecture": "ARM64", "is_arm64": True},
    )


# ── Optimization Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def sample_optimization_config() -> OptimizationConfig:
    """Create a sample optimization configuration."""
    return OptimizationConfig(
        model="tiny-llama-1.1b",
        objective="throughput",
        quantization_options=["FP16", "INT8", "INT4"],
        batch_sizes=[4, 8, 16],
        thread_counts=[2, 4],
        max_candidates=6,
        benchmark_per_candidate=3,
        max_tokens=128,
    )


@pytest.fixture
def sample_optimization_candidate() -> OptimizationCandidate:
    """Create a sample optimization candidate."""
    return OptimizationCandidate(
        id="cand-test01",
        name="INT4 | batch=8 | threads=4",
        description="Quantization: INT4, Batch Size: 8, Threads: 4",
        config={"quantization": "INT4", "batch_size": 8, "threads": 4},
        tokens_per_second=18.5,
        ttft_ms=65.0,
        memory_mb=1200.0,
        p95_latency_ms=900.0,
        status="completed",
    )


@pytest.fixture
def sample_optimization_result() -> OptimizationResult:
    """Create a sample optimization result."""
    return OptimizationResult(
        id="opt-test001",
        status="completed",
        config=OptimizationConfig(
            model="tiny-llama-1.1b",
            objective="throughput",
        ),
        timestamp=datetime.now(timezone.utc).isoformat(),
        candidates=[
            OptimizationCandidate(
                id="cand-001",
                name="FP16 | batch=4 | threads=2",
                description="",
                config={},
                tokens_per_second=10.0,
                ttft_ms=120.0,
                memory_mb=2000.0,
                p95_latency_ms=1500.0,
                status="completed",
            ),
            OptimizationCandidate(
                id="cand-002",
                name="INT4 | batch=8 | threads=4",
                description="",
                config={},
                tokens_per_second=18.5,
                ttft_ms=65.0,
                memory_mb=1200.0,
                p95_latency_ms=900.0,
                status="completed",
            ),
        ],
        best_candidate=OptimizationCandidate(
            id="cand-002",
            name="INT4 | batch=8 | threads=4",
            description="",
            config={},
            tokens_per_second=18.5,
            ttft_ms=65.0,
            memory_mb=1200.0,
            p95_latency_ms=900.0,
            status="completed",
        ),
        baseline={
            "tokens_per_second": 10.0,
            "ttft_ms": 120.0,
            "p95_latency_ms": 1500.0,
            "memory_mb": 2000.0,
        },
        improvement_summary={
            "tokens_per_second": {"before": 10.0, "after": 18.5, "change_percent": 85.0},
            "ttft_ms": {"before": 120.0, "after": 65.0, "change_percent": 45.8},
        },
        progress_percent=100.0,
        current_step="Optimization complete",
    )


# ── Recommendation Fixtures ───────────────────────────────────────────────────

@pytest.fixture
def sample_recommendation() -> Recommendation:
    """Create a sample recommendation."""
    return Recommendation(
        id="rec-test01",
        severity="warning",
        category="memory",
        problem="High memory consumption: 5000 MB",
        recommendation="Test INT8 quantization to reduce memory footprint",
        reason="Memory usage exceeds 4 GB, may cause swapping on constrained instances.",
        expected_goal="Reduce memory usage by 30-60% with quantization",
        suggested_config={"quantization": "INT8"},
        confidence=0.85,
    )


@pytest.fixture
def sample_recommendations() -> list[Recommendation]:
    """Create a list of sample recommendations."""
    return [
        Recommendation(
            id="rec-001",
            severity="warning",
            category="memory",
            problem="High memory consumption: 5000 MB",
            recommendation="Test INT8 quantization",
            reason="Memory usage exceeds 4 GB.",
            expected_goal="Reduce memory by 30-60%",
            confidence=0.85,
        ),
        Recommendation(
            id="rec-002",
            severity="info",
            category="cpu",
            problem="Low CPU utilization: 30%",
            recommendation="Increase thread count",
            reason="CPU is underutilized.",
            expected_goal="Increase CPU utilization to 60-80%",
            confidence=0.75,
        ),
        Recommendation(
            id="rec-003",
            severity="critical",
            category="latency",
            problem="P99 latency exceeds 1 second: 1200ms",
            recommendation="Reduce concurrency and batch size",
            reason="High tail latency indicates resource contention.",
            expected_goal="Bring P99 latency below 500ms",
            confidence=0.85,
        ),
    ]


# ── Report Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_report() -> ReportResponse:
    """Create a sample report response."""
    return ReportResponse(
        id="report-test01",
        format="markdown",
        content="# Benchmark Report\n\nTest report content.",
        timestamp=datetime.now(timezone.utc).isoformat(),
        benchmark_id="bench-test001",
    )


# ── Mock Runtime Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_runtime() -> MagicMock:
    """Create a mock inference runtime."""
    runtime = MagicMock()
    runtime.name = "llama.cpp"
    runtime.is_loaded.return_value = True
    runtime.generate.return_value = {
        "text": "ARM64 is a 64-bit processor architecture.",
        "prompt_tokens": 12,
        "completion_tokens": 10,
        "total_tokens": 22,
        "generation_time_ms": 800.0,
        "tokens_per_second": 12.5,
    }
    runtime.generate_stream.return_value = iter([
        {"token": "ARM64", "is_first": True, "is_last": False, "ttft_ms": 50.0},
        {"token": " is", "is_first": False, "is_last": False},
        {"token": " a", "is_first": False, "is_last": False},
        {"token": " 64-bit", "is_first": False, "is_last": False},
        {"token": " architecture.", "is_first": False, "is_last": True,
         "total_tokens": 5, "generation_time_ms": 500.0, "tokens_per_second": 10.0},
    ])
    runtime.get_model_info.return_value = {
        "path": "/models/test.gguf",
        "file_name": "test.gguf",
        "file_size_mb": 637.0,
        "n_ctx": 2048,
        "n_threads": 4,
        "n_batch": 512,
        "n_gpu_layers": 0,
        "load_time_ms": 1500.0,
    }
    return runtime


@pytest.fixture
def mock_inference_service(mock_runtime: MagicMock) -> MagicMock:
    """Create a mock inference service."""
    service = MagicMock()
    service.runtime = mock_runtime
    service.current_model = ModelInfo(
        id="test-model",
        name="Test Model",
        loaded=True,
    )
    service.get_status.return_value = {
        "model_loaded": True,
        "current_model": {"id": "test-model", "name": "Test Model"},
        "runtime": "llama.cpp",
        "model_info": {},
    }
    service.chat_completion.return_value = ChatCompletionResponse(
        id="chatcmpl-test123",
        created=int(datetime.now(timezone.utc).timestamp()),
        model="test-model",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="Test response"),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    return service


# ── Mock Storage Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_storage() -> MagicMock:
    """Create a mock storage instance."""
    storage = MagicMock()
    storage.get_benchmark.return_value = None
    storage.get_optimization.return_value = None
    storage.get_report.return_value = None
    storage.list_benchmarks.return_value = []
    storage.list_optimizations.return_value = []
    storage.list_reports.return_value = []
    return storage


# ── FastAPI Test Client Fixture ───────────────────────────────────────────────

@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application."""
    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_client(client: TestClient, sample_token_pair: TokenPair) -> TestClient:
    """Create an authenticated test client."""
    client.headers["Authorization"] = f"Bearer {sample_token_pair.access_token}"
    return client


# ── Hardware Mock Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def mock_hardware_info() -> dict[str, Any]:
    """Mock hardware info for testing."""
    return {
        "architecture": "ARM64",
        "is_arm64": True,
        "platform": "Linux",
        "platform_version": "5.15.0",
        "cpu_model": "ARM Neoverse N1",
        "cpu_count": 4,
        "cpu_count_physical": 4,
        "cpu_freq_mhz": 2400.0,
        "cpu_freq_max_mhz": 2400.0,
        "memory_total_gb": 8.0,
        "memory_available_gb": 5.0,
        "memory_used_percent": 37.5,
        "python_version": "3.11.0",
    }


@pytest.fixture
def mock_system_metrics() -> dict[str, Any]:
    """Mock system metrics for testing."""
    return {
        "cpu_utilization_percent": 45.0,
        "cpu_per_core_percent": [40.0, 50.0, 45.0, 45.0],
        "memory_used_mb": 3000.0,
        "memory_available_mb": 5000.0,
        "memory_total_mb": 8000.0,
        "memory_used_percent": 37.5,
    }


# ── CLI Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def cli_runner():
    """Create a CLI test runner (click.testing.CliRunner)."""
    try:
        from click.testing import CliRunner
        return CliRunner()
    except ImportError:
        pytest.skip("click not installed")
