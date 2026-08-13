"""
ArmPilot-AI — Cleanup Worker
Periodic maintenance worker for cache eviction, old data cleanup, and resource release.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings
from app.core.logger import logger


class CleanupWorker:
    """Periodic worker that performs maintenance tasks."""

    def __init__(self, interval_seconds: int = 3600) -> None:
        self._interval = interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._last_run: Optional[str] = None
        self._stats: dict[str, Any] = {
            "runs": 0,
            "files_cleaned": 0,
            "bytes_freed": 0,
            "errors": 0,
        }

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_run(self) -> Optional[str]:
        return self._last_run

    @property
    def stats(self) -> dict[str, Any]:
        return self._stats.copy()

    async def start(self) -> None:
        """Start the periodic cleanup loop."""
        if self._running:
            logger.warning("Cleanup worker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Cleanup worker started (interval=%ds)", self._interval)

    async def stop(self) -> None:
        """Stop the periodic cleanup loop."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Cleanup worker stopped")

    async def run_once(self) -> dict[str, Any]:
        """Run a single cleanup pass and return the results."""
        return await asyncio.get_event_loop().run_in_executor(None, self._do_cleanup)

    async def _run_loop(self) -> None:
        """Main periodic loop."""
        while self._running:
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break

            if not self._running:
                break

            try:
                await asyncio.get_event_loop().run_in_executor(None, self._do_cleanup)
            except Exception as e:
                logger.error("Cleanup worker error: %s", e)
                self._stats["errors"] += 1

    def _do_cleanup(self) -> dict[str, Any]:
        """Execute all cleanup tasks."""
        results: dict[str, Any] = {}
        self._stats["runs"] += 1
        self._last_run = datetime.now(timezone.utc).isoformat()

        logger.info("Cleanup worker running pass #%d", self._stats["runs"])

        results["temp_files"] = self._clean_temp_files()
        results["old_reports"] = self._clean_old_reports()
        results["empty_dirs"] = self._clean_empty_dirs()

        total_cleaned = sum(r.get("count", 0) for r in results.values())
        total_bytes = sum(r.get("bytes_freed", 0) for r in results.values())
        self._stats["files_cleaned"] += total_cleaned
        self._stats["bytes_freed"] += total_bytes

        logger.info(
            "Cleanup complete — %d files cleaned, %d bytes freed",
            total_cleaned, total_bytes,
        )

        return results

    def _clean_temp_files(self) -> dict[str, Any]:
        """Remove temporary files older than 24 hours."""
        import os

        temp_dir = settings.resolve_path(settings.data_dir) / "tmp"
        if not temp_dir.exists():
            return {"count": 0, "bytes_freed": 0}

        count = 0
        bytes_freed = 0
        now = time.time()
        cutoff = now - 86400  # 24 hours

        for path in temp_dir.rglob("*"):
            if path.is_file():
                try:
                    if path.stat().st_mtime < cutoff:
                        size = path.stat().st_size
                        path.unlink()
                        count += 1
                        bytes_freed += size
                except OSError as e:
                    logger.warning("Failed to remove %s: %s", path, e)
                    self._stats["errors"] += 1

        return {"count": count, "bytes_freed": bytes_freed}

    def _clean_old_reports(self) -> dict[str, Any]:
        """Remove report files older than 30 days."""
        reports_dir = settings.resolve_path(settings.reports_dir)
        if not reports_dir.exists():
            return {"count": 0, "bytes_freed": 0}

        count = 0
        bytes_freed = 0
        now = time.time()
        cutoff = now - (30 * 86400)  # 30 days

        for path in reports_dir.rglob("*"):
            if path.is_file():
                try:
                    if path.stat().st_mtime < cutoff:
                        size = path.stat().st_size
                        path.unlink()
                        count += 1
                        bytes_freed += size
                except OSError as e:
                    logger.warning("Failed to remove report %s: %s", path, e)
                    self._stats["errors"] += 1

        return {"count": count, "bytes_freed": bytes_freed}

    def _clean_empty_dirs(self) -> dict[str, Any]:
        """Remove empty directories under data and reports."""
        count = 0
        for base_name in ["data", "reports"]:
            base = settings.resolve_path(settings.base_dir / base_name)
            if not base.exists():
                continue
            for dirpath in sorted(base.rglob("*"), reverse=True):
                if dirpath.is_dir():
                    try:
                        if not any(dirpath.iterdir()):
                            dirpath.rmdir()
                            count += 1
                    except OSError:
                        pass

        return {"count": count, "bytes_freed": 0}


# Singleton
cleanup_worker = CleanupWorker()
