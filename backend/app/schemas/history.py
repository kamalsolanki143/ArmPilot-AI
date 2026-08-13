"""
ArmPilot-AI — History Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    """A single history entry (benchmark or optimization run)."""
    id: str
    type: str  # benchmark, optimization
    model: str
    config_summary: str
    status: str
    timestamp: str
    ttft_ms: Optional[float] = None
    tokens_per_second: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    memory_mb: Optional[float] = None


class HistoryResponse(BaseModel):
    """Response containing history entries."""
    entries: list[HistoryEntry] = Field(default_factory=list)
    total: int = 0
