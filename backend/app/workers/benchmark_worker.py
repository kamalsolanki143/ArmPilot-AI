"""
ArmPilot-AI — Benchmark Worker
Background worker that runs benchmark tasks asynchronously.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.logger import logger
from app.schemas.benchmark import BenchmarkConfig, BenchmarkResult


class BenchmarkWorker:
    """Background worker that manages benchmark execution queue."""

    def __init__(self) -> None:
        self._running = False
        self._current_task: Optional[asyncio.Task[None]] = None
        self._task_id: Optional[str] = None
        self._progress: dict[str, float] = {}
        self._history: list[dict[str, Any]] = []
        self._cancel_event = asyncio.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_task_id(self) -> Optional[str]:
        return self._task_id

    @property
    def progress(self) -> dict[str, float]:
        return self._progress.copy()

    @property
    def history(self) -> list[dict[str, Any]]:
        return self._history[-50:]

    async def start_benchmark(self, config: BenchmarkConfig) -> str:
        """Start a benchmark task in the background. Returns the task ID."""
        if self._running:
            raise RuntimeError("A benchmark task is already running")

        task_id = f"bench-worker-{uuid.uuid4().hex[:8]}"
        self._task_id = task_id
        self._progress[task_id] = 0.0
        self._cancel_event.clear()

        self._current_task = asyncio.create_task(
            self._run_benchmark(task_id, config)
        )
        return task_id

    async def cancel(self) -> bool:
        """Cancel the current benchmark task."""
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
        logger.info("Benchmark worker task cancelled")
        return True

    async def _run_benchmark(self, task_id: str, config: BenchmarkConfig) -> None:
        """Execute a benchmark run with progress tracking."""
        self._running = True
        start_time = datetime.now(timezone.utc)

        logger.info("Benchmark worker starting task %s (model=%s)", task_id, config.model)

        try:
            from app.benchmark.runner import benchmark_runner

            self._progress[task_id] = 10.0

            result = await benchmark_runner.run(config)

            if self._cancel_event.is_set():
                return

            self._progress[task_id] = 100.0

            self._history.append({
                "task_id": task_id,
                "benchmark_id": result.id,
                "model": config.model,
                "status": result.status,
                "timestamp": start_time.isoformat(),
                "tokens_per_second": result.tokens_per_second,
                "ttft_ms": result.ttft_ms,
            })

            logger.info(
                "Benchmark worker task %s completed — status=%s, TPS=%.1f",
                task_id, result.status, result.tokens_per_second or 0,
            )

        except asyncio.CancelledError:
            logger.info("Benchmark worker task %s cancelled", task_id)
            self._progress.pop(task_id, None)
            raise

        except Exception as e:
            logger.error("Benchmark worker task %s failed: %s", task_id, e)
            self._progress[task_id] = -1.0
            self._history.append({
                "task_id": task_id,
                "model": config.model,
                "status": "failed",
                "error": str(e),
                "timestamp": start_time.isoformat(),
            })

        finally:
            self._running = False
            self._current_task = None
            self._task_id = None

    def cleanup(self) -> None:
        """Clean up old history entries."""
        if len(self._history) > 100:
            self._history = self._history[-50:]


# Singleton
benchmark_worker = BenchmarkWorker()
