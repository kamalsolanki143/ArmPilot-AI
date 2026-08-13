"""
ArmPilot-AI — Benchmark API
"""

from __future__ import annotations

import asyncio
from fastapi import APIRouter, BackgroundTasks

from app.schemas.benchmark import BenchmarkConfig, BenchmarkRunRequest, BenchmarkRunResponse
from app.benchmark.runner import benchmark_runner
from app.database.storage import storage
from app.recommendation.engine import recommendation_engine
from app.core.exceptions import BenchmarkNotFoundError, BenchmarkRunningError
from app.core.logger import logger

router = APIRouter()


@router.post("/api/benchmark/run")
async def run_benchmark(request: BenchmarkRunRequest, background_tasks: BackgroundTasks):
    """Start a benchmark run."""
    if benchmark_runner.is_running:
        raise BenchmarkRunningError()

    # Run benchmark in background
    async def _run():
        result = await benchmark_runner.run(request.config)
        storage.save_benchmark(result.id, result.model_dump())

        # Auto-generate recommendations
        recs = recommendation_engine.analyze(result)
        if recs:
            storage.save_report(
                f"recs-{result.id}",
                {"benchmark_id": result.id, "recommendations": [r.model_dump() for r in recs]},
            )
            logger.info("Generated %d recommendations for %s", len(recs), result.id)

    background_tasks.add_task(asyncio.coroutine(_run) if False else _run)

    return BenchmarkRunResponse(
        success=True,
        benchmark_id="pending",
        message="Benchmark started. Poll /api/benchmark/latest for results.",
    )


@router.post("/api/benchmark/run/sync")
async def run_benchmark_sync(request: BenchmarkRunRequest):
    """Run benchmark synchronously and return results."""
    if benchmark_runner.is_running:
        raise BenchmarkRunningError()

    result = await benchmark_runner.run(request.config)
    storage.save_benchmark(result.id, result.model_dump())

    # Auto-generate recommendations
    recs = recommendation_engine.analyze(result)

    return {
        "success": True,
        "result": result.model_dump(),
        "recommendations": [r.model_dump() for r in recs],
    }


@router.get("/api/benchmark/{benchmark_id}")
async def get_benchmark(benchmark_id: str):
    """Get a specific benchmark result."""
    data = storage.get_benchmark(benchmark_id)
    if data is None:
        raise BenchmarkNotFoundError(benchmark_id)
    return {"success": True, "result": data}


@router.get("/api/benchmark/latest")
async def get_latest_benchmark():
    """Get the most recent benchmark result."""
    benchmarks = storage.list_benchmarks()
    if not benchmarks:
        return {"success": True, "result": None, "message": "No benchmarks found"}
    return {"success": True, "result": benchmarks[0]}


@router.get("/api/benchmarks")
async def list_benchmarks():
    """List all benchmark runs."""
    benchmarks = storage.list_benchmarks()
    return {"success": True, "results": benchmarks, "total": len(benchmarks)}
