"""
ArmPilot-AI — Optimization Engine
Generates candidate configurations, benchmarks each, and selects the best.
Runs as a non-blocking background task with progress tracking.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone
from itertools import product
from typing import Any, Optional

from app.core.config import settings
from app.core.logger import logger
from app.schemas.optimization import (
    OptimizationCandidate,
    OptimizationConfig,
    OptimizationResult,
)
from app.schemas.benchmark import BenchmarkConfig
from app.benchmark.runner import benchmark_runner


class OptimizationEngine:
    """Generates and tests optimization candidates as a background task."""

    def __init__(self) -> None:
        self._running = False
        self._current_id: str | None = None
        self._current_result: OptimizationResult | None = None
        self._task: asyncio.Task[OptimizationResult] | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_result(self) -> OptimizationResult | None:
        return self._current_result

    def generate_candidates(self, config: OptimizationConfig) -> list[OptimizationCandidate]:
        """Generate a list of candidate configurations to test."""
        candidates: list[OptimizationCandidate] = []

        combos = list(product(
            config.quantization_options,
            config.batch_sizes,
            config.thread_counts,
        ))

        combos = combos[:config.max_candidates]

        for i, (quant, batch, threads) in enumerate(combos):
            cand_id = f"cand-{uuid.uuid4().hex[:6]}"
            candidates.append(OptimizationCandidate(
                id=cand_id,
                name=f"{quant} | batch={batch} | threads={threads}",
                description=f"Quantization: {quant}, Batch Size: {batch}, Threads: {threads}",
                config={
                    "quantization": quant,
                    "batch_size": batch,
                    "threads": threads,
                    "model": config.model,
                },
            ))

        logger.info("Generated %d optimization candidates", len(candidates))
        return candidates

    def start(self, config: OptimizationConfig) -> str:
        """
        Start optimization as a background task (non-blocking).
        Returns the optimization ID immediately.
        """
        if self._running:
            raise RuntimeError("An optimization is already running")

        opt_id = f"opt-{uuid.uuid4().hex[:8]}"
        self._running = True
        self._current_id = opt_id

        self._current_result = OptimizationResult(
            id=opt_id,
            status="running",
            config=config,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self._task = asyncio.create_task(self._run_background(config, self._current_result))
        logger.info("Optimization %s dispatched as background task", opt_id)
        return opt_id

    async def _run_background(self, config: OptimizationConfig, result: OptimizationResult) -> OptimizationResult:
        """Execute the full optimization pipeline in the background."""
        opt_id = result.id
        bench_start = time.perf_counter()

        logger.info(
            "Optimization %s starting — model=%s, objective=%s",
            opt_id, config.model, config.objective,
        )

        try:
            result.candidates = self.generate_candidates(config)
            result.current_step = "Running baseline..."

            # Baseline benchmark
            baseline_config = BenchmarkConfig(
                model=config.model,
                num_requests=config.benchmark_per_candidate,
                max_tokens=config.max_tokens,
            )
            baseline_result = await benchmark_runner.run(baseline_config)
            result.baseline = {
                "ttft_ms": baseline_result.ttft_ms,
                "tokens_per_second": baseline_result.tokens_per_second,
                "p95_latency_ms": baseline_result.latency.p95_ms,
                "memory_mb": baseline_result.memory_mb,
                "benchmark_id": baseline_result.id,
            }

            # Test each candidate sequentially (benchmark_runner has its own concurrency)
            total = len(result.candidates)
            for i, candidate in enumerate(result.candidates):
                result.current_step = f"Testing candidate {i + 1}/{total}: {candidate.name}"
                result.progress_percent = round(((i + 1) / (total + 1)) * 100, 1)
                candidate.status = "testing"

                try:
                    bench_config = BenchmarkConfig(
                        model=config.model,
                        batch_size=candidate.config.get("batch_size", 512),
                        threads=candidate.config.get("threads", 4),
                        num_requests=config.benchmark_per_candidate,
                        max_tokens=config.max_tokens,
                    )

                    bench_result = await benchmark_runner.run(bench_config)
                    candidate.benchmark_id = bench_result.id
                    candidate.tokens_per_second = bench_result.tokens_per_second
                    candidate.ttft_ms = bench_result.ttft_ms
                    candidate.memory_mb = bench_result.memory_mb
                    candidate.p95_latency_ms = bench_result.latency.p95_ms
                    candidate.status = "completed"

                except Exception as e:
                    candidate.status = "failed"
                    logger.warning("Candidate %s failed: %s", candidate.id, e)

                # Yield control to the event loop
                await asyncio.sleep(0)

            # Select best candidate
            completed = [c for c in result.candidates if c.status == "completed"]
            if completed:
                result.best_candidate = self._select_best(completed, config.objective)
                result.improvement_summary = self._compute_improvements(
                    result.baseline, result.best_candidate
                )

            result.status = "completed"
            result.progress_percent = 100.0
            result.current_step = "Optimization complete"
            result.duration_seconds = round(time.perf_counter() - bench_start, 2)

            logger.info(
                "Optimization %s completed — best: %s (%.1fs)",
                opt_id,
                result.best_candidate.name if result.best_candidate else "none",
                result.duration_seconds,
            )

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            logger.error("Optimization %s failed: %s", opt_id, e)

        finally:
            self._running = False
            self._current_id = None
            self._task = None

        return result

    async def get_progress(self) -> dict[str, Any]:
        """Return current optimization progress (for polling)."""
        if not self._running or self._current_result is None:
            return {"running": False}
        return {
            "running": True,
            "id": self._current_id,
            "progress_percent": self._current_result.progress_percent,
            "current_step": self._current_result.current_step,
            "status": self._current_result.status,
        }

    async def await_result(self, timeout: float | None = None) -> OptimizationResult | None:
        """Wait for the background optimization to finish and return the result."""
        if self._task is None:
            return self._current_result
        try:
            await asyncio.wait_for(self._task, timeout=timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            return None
        return self._current_result

    def _select_best(
        self, candidates: list[OptimizationCandidate], objective: str
    ) -> OptimizationCandidate:
        """Select the best candidate based on the optimization objective."""
        if objective == "throughput":
            return max(candidates, key=lambda c: c.tokens_per_second or 0)
        elif objective == "latency":
            return min(candidates, key=lambda c: c.p95_latency_ms or float("inf"))
        elif objective == "memory":
            return min(candidates, key=lambda c: c.memory_mb or float("inf"))
        else:
            return max(candidates, key=lambda c: self._balanced_score(c))

    @staticmethod
    def _balanced_score(c: OptimizationCandidate) -> float:
        """Compute a balanced optimization score."""
        tps = c.tokens_per_second or 0
        ttft = c.ttft_ms or 999
        mem = c.memory_mb or 999
        p95 = c.p95_latency_ms or 999
        return tps * 0.4 + (1000 / max(ttft, 1)) * 0.2 + (1000 / max(p95, 1)) * 0.2 + (10000 / max(mem, 1)) * 0.2

    @staticmethod
    def _compute_improvements(
        baseline: dict[str, Any], best: OptimizationCandidate
    ) -> dict[str, Any]:
        """Compute improvement percentages."""
        improvements: dict[str, Any] = {}

        if baseline.get("tokens_per_second") and best.tokens_per_second:
            b = baseline["tokens_per_second"]
            improvements["tokens_per_second"] = {
                "before": b,
                "after": best.tokens_per_second,
                "change_percent": round(((best.tokens_per_second - b) / b) * 100, 1),
            }

        if baseline.get("ttft_ms") and best.ttft_ms:
            b = baseline["ttft_ms"]
            improvements["ttft_ms"] = {
                "before": b,
                "after": best.ttft_ms,
                "change_percent": round(((b - best.ttft_ms) / b) * 100, 1),
            }

        if baseline.get("p95_latency_ms") and best.p95_latency_ms:
            b = baseline["p95_latency_ms"]
            improvements["p95_latency_ms"] = {
                "before": b,
                "after": best.p95_latency_ms,
                "change_percent": round(((b - best.p95_latency_ms) / b) * 100, 1),
            }

        if baseline.get("memory_mb") and best.memory_mb:
            b = baseline["memory_mb"]
            improvements["memory_mb"] = {
                "before": b,
                "after": best.memory_mb,
                "change_percent": round(((b - best.memory_mb) / b) * 100, 1),
            }

        return improvements


# Singleton
optimization_engine = OptimizationEngine()
