"""
ArmPilot-AI — Structured Logging
"""

import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger("armpilot")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
