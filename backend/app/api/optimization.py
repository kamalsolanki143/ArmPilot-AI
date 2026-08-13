"""
ArmPilot-AI — Optimization API
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.schemas.optimization import OptimizationRunRequest, OptimizationRunResponse
from app.optimization.optimizer import optimization_engine
from app.database.storage import storage
from app.core.exceptions import OptimizationRunningError, OptimizationNotFoundError
from app.core.logger import logger

router = APIRouter()


@router.post("/api/optimization/run")
async def run_optimization(request: OptimizationRunRequest, background_tasks: BackgroundTasks):
    """Start an optimization run in the background. Returns immediately."""
    if optimization_engine.is_running:
        raise OptimizationRunningError()

    opt_id = optimization_engine.start(request.config)

    async def _run_and_save():
        result = await optimization_engine.await_result()
        if result:
            storage.save_optimization(result.id, result.model_dump())
            logger.info("Optimization %s saved to storage", result.id)

    background_tasks.add_task(_run_and_save)

    return OptimizationRunResponse(
        success=True,
        optimization_id=opt_id,
        message="Optimization started. Poll /api/optimization/{id} for progress.",
    )


@router.get("/api/optimization/progress")
async def get_optimization_progress():
    """Poll current optimization progress."""
    progress = await optimization_engine.get_progress()
    return {"success": True, **progress}


@router.get("/api/optimization/{opt_id}")
async def get_optimization(opt_id: str):
    """Get a specific optimization result."""
    data = storage.get_optimization(opt_id)
    if data is None:
        raise OptimizationNotFoundError(opt_id)
    return {"success": True, "result": data}


@router.get("/api/optimizations")
async def list_optimizations():
    """List all optimization runs."""
    optimizations = storage.list_optimizations()
    return {"success": True, "results": optimizations, "total": len(optimizations)}
