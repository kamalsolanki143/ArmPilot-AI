"""
ArmPilot-AI — Exception Handling
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ── Custom Exceptions ─────────────────────────────────────────────────────────

class ArmPilotError(Exception):
    """Base exception for all ArmPilot-AI errors."""

    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ModelNotFoundError(ArmPilotError):
    def __init__(self, model_id: str):
        super().__init__(
            code="MODEL_NOT_FOUND",
            message=f"Model '{model_id}' not found.",
            status_code=404,
        )


class ModelNotLoadedError(ArmPilotError):
    def __init__(self):
        super().__init__(
            code="MODEL_NOT_LOADED",
            message="No model is currently loaded. Load a model first.",
            status_code=503,
        )


class RuntimeNotAvailableError(ArmPilotError):
    def __init__(self, runtime: str):
        super().__init__(
            code="RUNTIME_NOT_AVAILABLE",
            message=f"Runtime '{runtime}' is not available or not installed.",
            status_code=503,
        )


class BenchmarkRunningError(ArmPilotError):
    def __init__(self):
        super().__init__(
            code="BENCHMARK_RUNNING",
            message="A benchmark is already running. Wait for it to complete.",
            status_code=409,
        )


class OptimizationRunningError(ArmPilotError):
    def __init__(self):
        super().__init__(
            code="OPTIMIZATION_RUNNING",
            message="An optimization is already running.",
            status_code=409,
        )


class InferenceError(ArmPilotError):
    def __init__(self, detail: str):
        super().__init__(
            code="INFERENCE_ERROR",
            message=f"Inference failed: {detail}",
            status_code=500,
        )


class BenchmarkNotFoundError(ArmPilotError):
    def __init__(self, benchmark_id: str):
        super().__init__(
            code="BENCHMARK_NOT_FOUND",
            message=f"Benchmark run '{benchmark_id}' not found.",
            status_code=404,
        )


class OptimizationNotFoundError(ArmPilotError):
    def __init__(self, optimization_id: str):
        super().__init__(
            code="OPTIMIZATION_NOT_FOUND",
            message=f"Optimization run '{optimization_id}' not found.",
            status_code=404,
        )


# ── Exception Handlers ───────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(ArmPilotError)
    async def armpilot_error_handler(_request: Request, exc: ArmPilotError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                },
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(_request: Request, exc: Exception):
        from app.core.logger import logger
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal server error occurred.",
                },
            },
        )
