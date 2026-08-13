"""
ArmPilot-AI — Reports API
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.database.storage import storage
from app.reports.report_builder import generate_benchmark_report, generate_optimization_report
from app.schemas.benchmark import BenchmarkResult
from app.schemas.optimization import OptimizationResult
from app.schemas.reports import ReportRequest, ReportResponse
from app.core.exceptions import BenchmarkNotFoundError, OptimizationNotFoundError

router = APIRouter()


@router.post("/api/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate a report from a benchmark or optimization run."""
    report_id = f"report-{uuid.uuid4().hex[:8]}"
    content = ""

    if request.benchmark_id:
        data = storage.get_benchmark(request.benchmark_id)
        if data is None:
            raise BenchmarkNotFoundError(request.benchmark_id)
        result = BenchmarkResult(**data)
        content = generate_benchmark_report(result)

    elif request.optimization_id:
        data = storage.get_optimization(request.optimization_id)
        if data is None:
            raise OptimizationNotFoundError(request.optimization_id)
        result = OptimizationResult(**data)
        content = generate_optimization_report(result)

    report = ReportResponse(
        id=report_id,
        format=request.format,
        content=content,
        timestamp=datetime.now(timezone.utc).isoformat(),
        benchmark_id=request.benchmark_id,
        optimization_id=request.optimization_id,
    )

    storage.save_report(report_id, report.model_dump())
    return {"success": True, "report": report.model_dump()}


@router.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """Get a specific report."""
    data = storage.get_report(report_id)
    if data is None:
        return {"success": False, "error": {"code": "REPORT_NOT_FOUND", "message": f"Report '{report_id}' not found."}}
    return {"success": True, "report": data}


@router.get("/api/reports")
async def list_reports():
    """List all reports."""
    reports = storage.list_reports()
    return {"success": True, "reports": reports, "total": len(reports)}
