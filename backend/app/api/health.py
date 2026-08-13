"""
ArmPilot-AI — Health API
"""

from fastapi import APIRouter

from app.core.config import settings
from app.services.inference_service import inference_service
from app.utils.hardware import get_hardware_info, get_system_metrics

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    hw = get_hardware_info()
    status = inference_service.get_status()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "model_loaded": status["model_loaded"],
        "current_model": status["current_model"]["id"] if status["current_model"] else None,
        "architecture": hw["architecture"],
        "is_arm64": hw["is_arm64"],
    }


@router.get("/api/metrics")
async def get_metrics():
    """Get current system metrics."""
    return {
        "success": True,
        "hardware": get_hardware_info(),
        "system": get_system_metrics(),
        "inference": inference_service.get_status(),
    }
