"""
ArmPilot-AI — Report Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Request to generate a report."""
    benchmark_id: Optional[str] = None
    optimization_id: Optional[str] = None
    format: str = Field(default="markdown", description="Output format: markdown, json, html, csv")
    include_charts: bool = True
    include_hardware: bool = True
    include_reproduction: bool = True


class ReportResponse(BaseModel):
    """Generated report."""
    id: str
    format: str
    content: str
    timestamp: str = ""
    benchmark_id: Optional[str] = None
    optimization_id: Optional[str] = None
