"""
ArmPilot-AI — JSON File Storage
Simple file-based storage for MVP. Stores benchmark runs, optimization runs, and reports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings
from app.core.logger import logger


class Storage:
    """JSON file-based storage for benchmark/optimization results."""

    def __init__(self) -> None:
        self._base_dir = settings.resolve_path(settings.data_dir)
        self._benchmarks_dir = self._base_dir / "benchmarks"
        self._optimizations_dir = self._base_dir / "optimizations"
        self._reports_dir = self._base_dir / "reports"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for d in [self._benchmarks_dir, self._optimizations_dir, self._reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ── Benchmark ─────────────────────────────────────────────────────────

    def save_benchmark(self, benchmark_id: str, data: dict[str, Any]) -> None:
        path = self._benchmarks_dir / f"{benchmark_id}.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.debug("Saved benchmark: %s", path)

    def get_benchmark(self, benchmark_id: str) -> Optional[dict[str, Any]]:
        path = self._benchmarks_dir / f"{benchmark_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_benchmarks(self) -> list[dict[str, Any]]:
        results = []
        for p in sorted(self._benchmarks_dir.glob("*.json"), reverse=True):
            try:
                results.append(json.loads(p.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return results

    # ── Optimization ──────────────────────────────────────────────────────

    def save_optimization(self, opt_id: str, data: dict[str, Any]) -> None:
        path = self._optimizations_dir / f"{opt_id}.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.debug("Saved optimization: %s", path)

    def get_optimization(self, opt_id: str) -> Optional[dict[str, Any]]:
        path = self._optimizations_dir / f"{opt_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_optimizations(self) -> list[dict[str, Any]]:
        results = []
        for p in sorted(self._optimizations_dir.glob("*.json"), reverse=True):
            try:
                results.append(json.loads(p.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return results

    # ── Reports ───────────────────────────────────────────────────────────

    def save_report(self, report_id: str, data: dict[str, Any]) -> None:
        path = self._reports_dir / f"{report_id}.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def get_report(self, report_id: str) -> Optional[dict[str, Any]]:
        path = self._reports_dir / f"{report_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_reports(self) -> list[dict[str, Any]]:
        results = []
        for p in sorted(self._reports_dir.glob("*.json"), reverse=True):
            try:
                results.append(json.loads(p.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return results


# Singleton
storage = Storage()
