"""
ArmPilot-AI — Health Monitor
Background health checks for inference runtime, system resources, and
service dependencies. Exposes a unified health status.
"""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any, Optional

from app.core.config import settings
from app.core.logger import logger
from app.utils.hardware import get_hardware_info, get_system_metrics, get_process_metrics


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Health status for a single component."""

    __slots__ = ("name", "status", "message", "latency_ms", "last_checked", "metadata")

    def __init__(self, name: str) -> None:
        self.name = name
        self.status = HealthStatus.HEALTHY
        self.message = ""
        self.latency_ms: float = 0.0
        self.last_checked: float = 0.0
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "last_checked": self.last_checked,
            "metadata": self.metadata,
        }


class HealthMonitor:
    """Monitors application health across key subsystems."""

    def __init__(self) -> None:
        self._components: dict[str, ComponentHealth] = {}
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._interval_seconds = 30.0

        # Register components
        for name in ("inference", "system", "memory", "disk"):
            self._components[name] = ComponentHealth(name)

    @property
    def overall_status(self) -> HealthStatus:
        """Determine overall health from component statuses."""
        statuses = [c.status for c in self._components.values()]
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def get_health(self) -> dict[str, Any]:
        """Return current health report."""
        return {
            "status": self.overall_status.value,
            "components": {name: ch.to_dict() for name, ch in self._components.items()},
            "timestamp": time.time(),
        }

    def check_inference(self) -> ComponentHealth:
        """Check inference runtime health."""
        ch = self._components["inference"]
        start = time.perf_counter()

        try:
            from app.services.inference_service import inference_service
            status = inference_service.get_status()
            loaded = status.get("model_loaded", False)
            model = status.get("current_model")

            ch.metadata = {
                "model_loaded": loaded,
                "current_model": model.get("id") if model else None,
                "runtime": status.get("runtime"),
            }

            if loaded:
                ch.status = HealthStatus.HEALTHY
                ch.message = f"Model loaded: {model.get('id', 'unknown')}"
            else:
                ch.status = HealthStatus.DEGRADED
                ch.message = "No model loaded"

        except Exception as exc:
            ch.status = HealthStatus.UNHEALTHY
            ch.message = f"Inference check failed: {exc}"

        ch.latency_ms = (time.perf_counter() - start) * 1000
        ch.last_checked = time.time()
        return ch

    def check_system(self) -> ComponentHealth:
        """Check system resource health."""
        ch = self._components["system"]
        start = time.perf_counter()

        try:
            metrics = get_system_metrics()
            cpu = metrics["cpu_utilization_percent"]
            mem_pct = metrics["memory_used_percent"]

            ch.metadata = {
                "cpu_percent": cpu,
                "memory_percent": mem_pct,
                "memory_used_mb": metrics["memory_used_mb"],
            }

            if cpu > 95 or mem_pct > 95:
                ch.status = HealthStatus.UNHEALTHY
                ch.message = f"Critical: CPU {cpu:.0f}%, Memory {mem_pct:.0f}%"
            elif cpu > 80 or mem_pct > 85:
                ch.status = HealthStatus.DEGRADED
                ch.message = f"High usage: CPU {cpu:.0f}%, Memory {mem_pct:.0f}%"
            else:
                ch.status = HealthStatus.HEALTHY
                ch.message = f"CPU {cpu:.0f}%, Memory {mem_pct:.0f}%"

        except Exception as exc:
            ch.status = HealthStatus.UNHEALTHY
            ch.message = f"System check failed: {exc}"

        ch.latency_ms = (time.perf_counter() - start) * 1000
        ch.last_checked = time.time()
        return ch

    def check_memory(self) -> ComponentHealth:
        """Check process memory usage."""
        ch = self._components["memory"]
        start = time.perf_counter()

        try:
            proc = get_process_metrics()
            rss_mb = proc.get("memory_rss_mb", 0)
            ch.metadata = {
                "rss_mb": rss_mb,
                "vms_mb": proc.get("memory_vms_mb", 0),
                "threads": proc.get("num_threads", 0),
            }

            # Warn if process RSS exceeds 4 GB
            if rss_mb > 4096:
                ch.status = HealthStatus.DEGRADED
                ch.message = f"Process RSS {rss_mb:.0f} MB — consider model optimization"
            else:
                ch.status = HealthStatus.HEALTHY
                ch.message = f"Process RSS {rss_mb:.0f} MB"

        except Exception as exc:
            ch.status = HealthStatus.UNHEALTHY
            ch.message = f"Memory check failed: {exc}"

        ch.latency_ms = (time.perf_counter() - start) * 1000
        ch.last_checked = time.time()
        return ch

    def check_disk(self) -> ComponentHealth:
        """Check disk space for models and reports directories."""
        ch = self._components["disk"]
        start = time.perf_counter()

        try:
            import shutil
            base = settings.resolve_path(settings.base_dir)
            usage = shutil.disk_usage(str(base))
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            used_pct = (usage.used / usage.total) * 100

            ch.metadata = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_pct, 1),
            }

            if free_gb < 1.0:
                ch.status = HealthStatus.UNHEALTHY
                ch.message = f"Critical: {free_gb:.1f} GB free"
            elif free_gb < 5.0:
                ch.status = HealthStatus.DEGRADED
                ch.message = f"Low disk: {free_gb:.1f} GB free"
            else:
                ch.status = HealthStatus.HEALTHY
                ch.message = f"{free_gb:.1f} GB free of {total_gb:.1f} GB"

        except Exception as exc:
            ch.status = HealthStatus.UNHEALTHY
            ch.message = f"Disk check failed: {exc}"

        ch.latency_ms = (time.perf_counter() - start) * 1000
        ch.last_checked = time.time()
        return ch

    def run_all_checks(self) -> dict[str, Any]:
        """Run all health checks and return the full report."""
        self.check_inference()
        self.check_system()
        self.check_memory()
        self.check_disk()
        return self.get_health()

    async def start_background(self, interval_seconds: float = 30.0) -> None:
        """Start periodic background health checks."""
        if self._running:
            return
        self._running = True
        self._interval_seconds = interval_seconds
        self._task = asyncio.create_task(self._background_loop())
        logger.info("Health monitor started (interval=%ds)", interval_seconds)

    async def stop_background(self) -> None:
        """Stop background health checks."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Health monitor stopped")

    async def _background_loop(self) -> None:
        while self._running:
            try:
                report = self.run_all_checks()
                status = report["status"]
                if status != "healthy":
                    logger.warning("Health check: %s", status)
                    for name, comp in report["components"].items():
                        if comp["status"] != "healthy":
                            logger.warning("  %s: %s", name, comp["message"])
            except Exception as exc:
                logger.error("Health check loop error: %s", exc)
            await asyncio.sleep(self._interval_seconds)


# Singleton
health_monitor = HealthMonitor()
