"""
ArmPilot-AI — Report Export Manager
Unified interface for generating reports in multiple formats.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings
from app.core.logger import logger
from app.database.storage import storage
from app.schemas.benchmark import BenchmarkResult
from app.schemas.optimization import OptimizationResult
from app.schemas.reports import ReportRequest, ReportResponse


class ReportExporter:
    """Manages report generation across formats (markdown, HTML, CSV, PDF, JSON)."""

    SUPPORTED_FORMATS = ("markdown", "html", "csv", "pdf", "json")

    def generate(
        self,
        request: ReportRequest,
    ) -> ReportResponse:
        """Generate a report from a request and persist it to storage."""
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        ts = datetime.now(timezone.utc).isoformat()
        content = ""

        if request.benchmark_id:
            content = self._generate_benchmark(
                request.benchmark_id,
                fmt=request.format,
                include_charts=request.include_charts,
                include_hardware=request.include_hardware,
                include_reproduction=request.include_reproduction,
            )
        elif request.optimization_id:
            content = self._generate_optimization(
                request.optimization_id,
                fmt=request.format,
                include_charts=request.include_charts,
                include_hardware=request.include_hardware,
                include_reproduction=request.include_reproduction,
            )

        report = ReportResponse(
            id=report_id,
            format=request.format,
            content=content,
            timestamp=ts,
            benchmark_id=request.benchmark_id,
            optimization_id=request.optimization_id,
        )

        storage.save_report(report_id, report.model_dump())
        logger.info("Report %s generated (%s)", report_id, request.format)
        return report

    def generate_benchmark(
        self,
        benchmark_id: str,
        fmt: str = "markdown",
        *,
        include_charts: bool = True,
        include_hardware: bool = True,
        include_reproduction: bool = True,
    ) -> ReportResponse:
        """Generate a benchmark report with full control over options."""
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        ts = datetime.now(timezone.utc).isoformat()

        content = self._generate_benchmark(
            benchmark_id, fmt, include_charts, include_hardware, include_reproduction
        )

        report = ReportResponse(
            id=report_id,
            format=fmt,
            content=content,
            timestamp=ts,
            benchmark_id=benchmark_id,
        )
        storage.save_report(report_id, report.model_dump())
        return report

    def generate_optimization(
        self,
        optimization_id: str,
        fmt: str = "markdown",
        *,
        include_charts: bool = True,
        include_hardware: bool = True,
        include_reproduction: bool = True,
    ) -> ReportResponse:
        """Generate an optimization report with full control over options."""
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        ts = datetime.now(timezone.utc).isoformat()

        content = self._generate_optimization(
            optimization_id, fmt, include_charts, include_hardware, include_reproduction
        )

        report = ReportResponse(
            id=report_id,
            format=fmt,
            content=content,
            timestamp=ts,
            optimization_id=optimization_id,
        )
        storage.save_report(report_id, report.model_dump())
        return report

    # ── Internal dispatchers ─────────────────────────────────────────────

    def _generate_benchmark(
        self,
        benchmark_id: str,
        fmt: str,
        include_charts: bool,
        include_hardware: bool,
        include_reproduction: bool,
    ) -> str:
        data = storage.get_benchmark(benchmark_id)
        if data is None:
            raise ValueError(f"Benchmark '{benchmark_id}' not found")
        result = BenchmarkResult(**data)

        if fmt == "html":
            from app.reports.html import generate_benchmark_html
            return generate_benchmark_html(
                result,
                include_charts=include_charts,
                include_hardware=include_hardware,
                include_reproduction=include_reproduction,
            )
        elif fmt == "csv":
            from app.reports.csv import generate_benchmark_csv
            return generate_benchmark_csv(result)
        elif fmt == "pdf":
            from app.reports.pdf import generate_benchmark_pdf
            pdf_bytes = generate_benchmark_pdf(
                result,
                include_charts=include_charts,
                include_hardware=include_hardware,
                include_reproduction=include_reproduction,
            )
            # Store PDF and return path
            pdf_path = settings.resolve_path(settings.reports_dir) / f"{benchmark_id}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            return f"PDF saved to {pdf_path}"
        elif fmt == "json":
            import json
            return json.dumps(result.model_dump(), indent=2, default=str)
        else:
            from app.reports.report_builder import generate_benchmark_report
            return generate_benchmark_report(result)

    def _generate_optimization(
        self,
        optimization_id: str,
        fmt: str,
        include_charts: bool,
        include_hardware: bool,
        include_reproduction: bool,
    ) -> str:
        data = storage.get_optimization(optimization_id)
        if data is None:
            raise ValueError(f"Optimization '{optimization_id}' not found")
        result = OptimizationResult(**data)

        if fmt == "html":
            from app.reports.html import generate_optimization_html
            return generate_optimization_html(
                result,
                include_charts=include_charts,
                include_hardware=include_hardware,
                include_reproduction=include_reproduction,
            )
        elif fmt == "csv":
            from app.reports.csv import generate_optimization_csv
            return generate_optimization_csv(result)
        elif fmt == "pdf":
            from app.reports.pdf import generate_optimization_pdf
            pdf_bytes = generate_optimization_pdf(
                result,
                include_charts=include_charts,
                include_reproduction=include_reproduction,
            )
            pdf_path = settings.resolve_path(settings.reports_dir) / f"{optimization_id}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            return f"PDF saved to {pdf_path}"
        elif fmt == "json":
            import json
            return json.dumps(result.model_dump(), indent=2, default=str)
        else:
            from app.reports.report_builder import generate_optimization_report
            return generate_optimization_report(result)


# Singleton
report_exporter = ReportExporter()
