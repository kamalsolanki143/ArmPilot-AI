"""
ArmPilot-AI — Report Worker
Background worker that generates reports in various formats.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.logger import logger
from app.schemas.reports import ReportRequest, ReportResponse


class ReportWorker:
    """Background worker that generates reports asynchronously."""

    def __init__(self) -> None:
        self._running = False
        self._current_task: Optional[asyncio.Task[None]] = None
        self._task_id: Optional[str] = None
        self._progress: dict[str, float] = {}
        self._completed_reports: list[dict[str, Any]] = []
        self._cancel_event = asyncio.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_task_id(self) -> Optional[str]:
        return self._task_id

    @property
    def progress(self) -> dict[str, Any]:
        return {
            "task_id": self._task_id,
            "running": self._running,
            "percent": self._progress.get(self._task_id or "", 0.0) if self._task_id else 0.0,
        }

    @property
    def completed_reports(self) -> list[dict[str, Any]]:
        return self._completed_reports[-50:]

    async def start_report(self, request: ReportRequest) -> str:
        """Start report generation in the background. Returns the task ID."""
        if self._running:
            raise RuntimeError("A report generation task is already running")

        task_id = f"report-{uuid.uuid4().hex[:8]}"
        self._task_id = task_id
        self._progress[task_id] = 0.0
        self._cancel_event.clear()

        self._current_task = asyncio.create_task(
            self._generate_report(task_id, request)
        )
        return task_id

    async def cancel(self) -> bool:
        """Cancel the current report generation task."""
        if not self._running or self._current_task is None:
            return False
        self._cancel_event.set()
        self._current_task.cancel()
        try:
            await self._current_task
        except asyncio.CancelledError:
            pass
        self._running = False
        self._current_task = None
        self._task_id = None
        logger.info("Report worker task cancelled")
        return True

    async def _generate_report(self, task_id: str, request: ReportRequest) -> None:
        """Generate a report in the specified format."""
        self._running = True
        start_time = datetime.now(timezone.utc)

        logger.info(
            "Report worker starting task %s (format=%s, benchmark=%s)",
            task_id, request.format, request.benchmark_id,
        )

        try:
            self._progress[task_id] = 20.0

            content = await asyncio.get_event_loop().run_in_executor(
                None, self._build_report_content, request
            )

            if self._cancel_event.is_set():
                return

            self._progress[task_id] = 80.0

            report = ReportResponse(
                id=task_id,
                format=request.format,
                content=content,
                timestamp=start_time.isoformat(),
                benchmark_id=request.benchmark_id,
                optimization_id=request.optimization_id,
            )

            self._progress[task_id] = 100.0

            self._completed_reports.append({
                "task_id": task_id,
                "report_id": report.id,
                "format": report.format,
                "benchmark_id": report.benchmark_id,
                "optimization_id": report.optimization_id,
                "timestamp": report.timestamp,
                "content_length": len(content),
            })

            logger.info(
                "Report worker task %s completed — format=%s, length=%d",
                task_id, request.format, len(content),
            )

        except asyncio.CancelledError:
            logger.info("Report worker task %s cancelled", task_id)
            self._progress.pop(task_id, None)
            raise

        except Exception as e:
            logger.error("Report worker task %s failed: %s", task_id, e)
            self._progress[task_id] = -1.0
            self._completed_reports.append({
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": start_time.isoformat(),
            })

        finally:
            self._running = False
            self._current_task = None
            self._task_id = None

    def _build_report_content(self, request: ReportRequest) -> str:
        """Build report content by delegating to the appropriate report builder."""
        from app.reports.report_builder import generate_benchmark_report, generate_optimization_report
        from app.services.benchmark_service import benchmark_service
        from app.services.optimization_service import optimization_service

        if request.benchmark_id:
            result = benchmark_service.get_result(request.benchmark_id)
            if result is None:
                raise ValueError(f"Benchmark {request.benchmark_id} not found")
            return generate_benchmark_report(result)

        if request.optimization_id:
            result = optimization_service.get_result(request.optimization_id)
            if result is None:
                raise ValueError(f"Optimization {request.optimization_id} not found")
            return generate_optimization_report(result)

        raise ValueError("Either benchmark_id or optimization_id must be provided")

    def cleanup(self) -> None:
        """Clean up old completed reports."""
        if len(self._completed_reports) > 100:
            self._completed_reports = self._completed_reports[-50:]


# Singleton
report_worker = ReportWorker()
