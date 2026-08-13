"""
ArmPilot-AI — Optimization Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class OptimizationCandidate(BaseModel):
    """A single optimization configuration to test."""
    id: str
    name: str
    description: str
    config: dict = Field(default_factory=dict)
    # Set after benchmarking
    benchmark_id: Optional[str] = None
    tokens_per_second: Optional[float] = None
    ttft_ms: Optional[float] = None
    memory_mb: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    status: str = "pending"  # pending, testing, completed, failed


class OptimizationConfig(BaseModel):
    """Configuration for an optimization run."""
    model: str = Field(..., description="Model ID")
    objective: str = Field(default="throughput", description="Optimization objective: throughput, latency, memory, balanced")
    quantization_options: list[str] = Field(default=["FP16", "INT8", "INT4"])
    batch_sizes: list[int] = Field(default=[1, 4, 8])
    thread_counts: list[int] = Field(default=[2, 4, 8])
    max_candidates: int = Field(default=8, ge=1)
    benchmark_per_candidate: int = Field(default=5, ge=1)
    max_tokens: int = Field(default=128, ge=1)


class OptimizationResult(BaseModel):
    """Result of a full optimization run."""
    id: str
    status: str = "pending"  # pending, running, completed, failed
    config: OptimizationConfig
    timestamp: str = ""

    candidates: list[OptimizationCandidate] = Field(default_factory=list)
    best_candidate: Optional[OptimizationCandidate] = None
    baseline: Optional[dict] = None
    improvement_summary: Optional[dict] = None

    progress_percent: float = 0.0
    current_step: str = ""
    error: Optional[str] = None

    duration_seconds: Optional[float] = None


class OptimizationRunRequest(BaseModel):
    """Request to start an optimization run."""
    config: OptimizationConfig


class OptimizationRunResponse(BaseModel):
    """Response when starting an optimization."""
    success: bool
    optimization_id: str
    message: str
