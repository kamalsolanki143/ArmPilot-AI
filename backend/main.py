"""
ArmPilot-AI — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middleware
from app.core.startup import on_startup
from app.core.shutdown import on_shutdown
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    await on_startup()
    yield
    await on_shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Arm64-first LLM inference optimization and benchmarking platform. "
            "Deploy, benchmark, optimize, and compare open-source LLMs on Arm infrastructure."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Register middleware
    register_middleware(app)

    # Register exception handlers
    register_exception_handlers(app)

    # Mount API routes
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
