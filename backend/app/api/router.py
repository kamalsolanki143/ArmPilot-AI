"""
ArmPilot-AI — API Router
Central router that mounts all API sub-routers.
"""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.inference import router as inference_router
from app.api.benchmark import router as benchmark_router
from app.api.optimization import router as optimization_router
from app.api.recommendation import router as recommendation_router
from app.api.reports import router as reports_router
from app.api.history import router as history_router
from app.api.auth import router as auth_router

api_router = APIRouter()

# Mount all sub-routers
api_router.include_router(auth_router, tags=["Auth"])
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(inference_router, tags=["Inference"])
api_router.include_router(benchmark_router, tags=["Benchmark"])
api_router.include_router(optimization_router, tags=["Optimization"])
api_router.include_router(recommendation_router, tags=["Recommendations"])
api_router.include_router(reports_router, tags=["Reports"])
api_router.include_router(history_router, tags=["History"])
