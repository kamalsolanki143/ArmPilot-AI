"""
ArmPilot-AI — Benchmark Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class BenchmarkConfig(BaseModel):
    """Configuration for a benchmark run."""
    model: str = Field(..., description="Model ID to benchmark")
    runtime: str = Field(default="llama.cpp")
    quantization: Optional[str] = None
    batch_size: int = Field(default=512, ge=1)
    threads: int = Field(default=4, ge=1)
    concurrency: int = Field(default=1, ge=1)
    duration_seconds: int = Field(default=60, ge=5)
    num_requests: int = Field(default=10, ge=1)
    prompt: str = Field(default="Explain the benefits of ARM64 architecture for AI inference.")
    prompt_length: Optional[int] = None
    max_tokens: int = Field(default=128, ge=1)
    warmup_requests: int = Field(default=3, ge=0)
    cpu_affinity: Optional[list[int]] = None
    kv_cache_size: Optional[int] = None


class LatencyMetrics(BaseModel):
    """Latency percentile measurements."""
    p50_ms: float = 0.0
    p75_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0


class BenchmarkResult(BaseModel):
    """Result of a single benchmark run."""
    id: str
    status: str = "pending"  # pending, running, completed, failed
    config: BenchmarkConfig
    timestamp: str = ""

    # Core metrics
    ttft_ms: Optional[float] = None
    tokens_per_second: Optional[float] = None
    requests_per_second: Optional[float] = None
    total_tokens: int = 0
    total_requests: int = 0

    # Latency
    latency: LatencyMetrics = Field(default_factory=LatencyMetrics)

    # Resource usage
    cpu_utilization_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    model_size_mb: Optional[float] = None

    # Hardware context
    hardware: Optional[dict] = None

    # Timing
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class BenchmarkRunRequest(BaseModel):
    """Request to start a benchmark run."""
    config: BenchmarkConfig


class BenchmarkRunResponse(BaseModel):
    """Response when starting a benchmark."""
    success: bool
    benchmark_id: str
    message: str


class BenchmarkComparison(BaseModel):
    """Before/after comparison of two benchmark runs."""
    baseline: BenchmarkResult
    optimized: BenchmarkResult
    improvements: dict[str, float] = Field(default_factory=dict)
