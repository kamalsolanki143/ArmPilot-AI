"""
ArmPilot-AI — Recommendation Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """A single actionable recommendation."""
    id: str
    severity: str = "info"  # info, warning, critical
    category: str  # memory, cpu, latency, throughput, configuration
    problem: str
    recommendation: str
    reason: str
    expected_goal: str
    suggested_config: Optional[dict] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class RecommendationRequest(BaseModel):
    """Request for recommendations (optionally based on a benchmark run)."""
    benchmark_id: Optional[str] = None
    model: Optional[str] = None
    current_config: Optional[dict] = None


class RecommendationResponse(BaseModel):
    """Response containing generated recommendations."""
    success: bool
    recommendations: list[Recommendation] = Field(default_factory=list)
    analyzed_benchmark_id: Optional[str] = None
    timestamp: str = ""
