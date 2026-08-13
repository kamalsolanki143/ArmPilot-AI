"""
ArmPilot-AI — Shutdown Events
"""

from app.core.logger import logger


async def on_shutdown() -> None:
    """Execute shutdown/cleanup tasks."""
    logger.info("Shutting down ArmPilot-AI...")

    # Unload any active inference runtime
    from app.services.inference_service import inference_service
    if inference_service.runtime is not None:
        try:
            inference_service.unload()
            logger.info("Model unloaded")
        except Exception as e:
            logger.warning("Error unloading model during shutdown: %s", e)

    logger.info("Shutdown complete")
