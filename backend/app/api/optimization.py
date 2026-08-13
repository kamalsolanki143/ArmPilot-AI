"""
ArmPilot-AI — Optimization API
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.schemas.optimization import OptimizationRunRequest, OptimizationRunResponse
from app.optimization.optimizer import optimization_engine
from app.database.storage import storage
from app.core.exceptions import OptimizationRunningError, OptimizationNotFoundError

router = APIRouter()


@router.post("/api/optimization/run")
async def run_optimization(request: OptimizationRunRequest):
    """Run an optimization synchronously."""
    if optimization_engine.is_running:
        raise OptimizationRunningError()

    result = await optimization_engine.run(request.config)
    storage.save_optimization(result.id, result.model_dump())

    return {
        "success": True,
        "result": result.model_dump(),
    }


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
