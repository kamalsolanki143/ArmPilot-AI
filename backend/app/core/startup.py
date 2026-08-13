"""
ArmPilot-AI — Startup Events
"""

from app.core.config import settings
from app.core.logger import logger


async def on_startup() -> None:
    """Execute startup tasks."""
    logger.info("=" * 60)
    logger.info("  %s v%s starting", settings.app_name, settings.app_version)
    logger.info("=" * 60)

    # Ensure required directories exist
    for dir_path in [settings.models_dir, settings.data_dir, settings.reports_dir]:
        resolved = settings.resolve_path(dir_path)
        resolved.mkdir(parents=True, exist_ok=True)
        logger.info("Directory ready: %s", resolved)

    # Log hardware information
    from app.utils.hardware import get_hardware_info
    hw = get_hardware_info()
    logger.info("Hardware: %s | %s cores | %.1f GB RAM | %s",
                hw["architecture"], hw["cpu_count"],
                hw["memory_total_gb"], hw["cpu_model"])

    logger.info("Server: http://%s:%d", settings.host, settings.port)
    logger.info("Startup complete")
