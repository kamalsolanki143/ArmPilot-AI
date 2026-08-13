"""
ArmPilot-AI — Optimization Worker
Background worker that runs optimization sweeps asynchronously.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.logger import logger
from app.schemas.optimization import OptimizationConfig, OptimizationResult


class OptimizationWorker:
    """Background worker that manages optimization task execution."""

    def __init__(self) -> None:
        self._running = False
        self._current_task: Optional[asyncio.Task[None]] = None
        self._task_id: Optional[str] = None
        self._progress: dict[str, float] = {}
        self._current_step: str = ""
        self._history: list[dict[str, Any]] = []
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
            "step": self._current_step,
            "percent": self._progress.get(self._task_id or "", 0.0) if self._task_id else 0.0,
        }

    @property
    def history(self) -> list[dict[str, Any]]:
        return self._history[-50:]

    async def start_optimization(self, config: OptimizationConfig) -> str:
        """Start an optimization sweep in the background. Returns the task ID."""
        if self._running:
            raise RuntimeError("An optimization task is already running")

        task_id = f"opt-worker-{uuid.uuid4().hex[:8]}"
        self._task_id = task_id
        self._progress[task_id] = 0.0
        self._current_step = "Initializing"
        self._cancel_event.clear()

        self._current_task = asyncio.create_task(
            self._run_optimization(task_id, config)
        )
        return task_id

    async def cancel(self) -> bool:
        """Cancel the current optimization task."""
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
        self._current_step = ""
        logger.info("Optimization worker task cancelled")
        return True

    async def _run_optimization(self, task_id: str, config: OptimizationConfig) -> None:
        """Execute the optimization sweep with progress tracking."""
        self._running = True
        start_time = datetime.now(timezone.utc)

        logger.info(
            "Optimization worker starting task %s (model=%s, objective=%s)",
            task_id, config.model, config.objective,
        )

        try:
            from app.services.optimization_service import optimization_service

            self._progress[task_id] = 10.0
            self._current_step = "Generating candidates"

            if self._cancel_event.is_set():
                return

            self._progress[task_id] = 30.0
            self._current_step = "Running baseline benchmark"

            if self._cancel_event.is_set():
                return

            self._progress[task_id] = 50.0
            self._current_step = "Testing candidates"

            result = await optimization_service.run_optimization(config)

            if self._cancel_event.is_set():
                return

            self._progress[task_id] = 100.0
            self._current_step = "Completed"

            self._history.append({
                "task_id": task_id,
                "optimization_id": result.id,
                "model": config.model,
                "objective": config.objective,
                "status": result.status,
                "candidates_tested": len(result.candidates),
                "timestamp": start_time.isoformat(),
                "best_tps": result.best_candidate.tokens_per_second if result.best_candidate else None,
            })

            logger.info(
                "Optimization worker task %s completed — %d candidates tested",
                task_id, len(result.candidates),
            )

        except asyncio.CancelledError:
            logger.info("Optimization worker task %s cancelled", task_id)
            self._progress.pop(task_id, None)
            self._current_step = ""
            raise

        except Exception as e:
            logger.error("Optimization worker task %s failed: %s", task_id, e)
            self._progress[task_id] = -1.0
            self._current_step = "Failed"
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
optimization_worker = OptimizationWorker()
