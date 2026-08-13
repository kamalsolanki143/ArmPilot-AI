"""
ArmPilot-AI — Hardware Detection Utilities
"""

import platform
import os
from typing import Any

import psutil


def get_hardware_info() -> dict[str, Any]:
    """Detect and return current hardware information."""
    mem = psutil.virtual_memory()
    cpu_freq = psutil.cpu_freq()

    # Detect CPU model
    cpu_model = _detect_cpu_model()

    # Detect architecture
    arch = platform.machine().upper()
    is_arm = arch in ("AARCH64", "ARM64", "ARMV8", "ARMV8L")

    return {
        "architecture": arch,
        "is_arm64": is_arm,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "cpu_model": cpu_model,
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_freq_mhz": cpu_freq.current if cpu_freq else None,
        "cpu_freq_max_mhz": cpu_freq.max if cpu_freq else None,
        "memory_total_gb": round(mem.total / (1024 ** 3), 2),
        "memory_available_gb": round(mem.available / (1024 ** 3), 2),
        "memory_used_percent": mem.percent,
        "python_version": platform.python_version(),
    }


def get_system_metrics() -> dict[str, Any]:
    """Get current system resource utilization."""
    mem = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)

    return {
        "cpu_utilization_percent": cpu_percent,
        "cpu_per_core_percent": cpu_per_core,
        "memory_used_mb": round(mem.used / (1024 ** 2), 1),
        "memory_available_mb": round(mem.available / (1024 ** 2), 1),
        "memory_total_mb": round(mem.total / (1024 ** 2), 1),
        "memory_used_percent": mem.percent,
    }


def get_process_metrics(pid: int | None = None) -> dict[str, Any]:
    """Get resource usage for a specific process."""
    try:
        proc = psutil.Process(pid or os.getpid())
        mem_info = proc.memory_info()
        return {
            "pid": proc.pid,
            "cpu_percent": proc.cpu_percent(interval=0.1),
            "memory_rss_mb": round(mem_info.rss / (1024 ** 2), 1),
            "memory_vms_mb": round(mem_info.vms / (1024 ** 2), 1),
            "num_threads": proc.num_threads(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {}


def _detect_cpu_model() -> str:
    """Try to detect a human-readable CPU model string."""
    system = platform.system()

    if system == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.strip().startswith("model name"):
                        return line.split(":")[1].strip()
                    if line.strip().startswith("Model"):
                        return line.split(":")[1].strip()
        except (FileNotFoundError, PermissionError):
            pass

    elif system == "Darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

    elif system == "Windows":
        try:
            return platform.processor() or "Unknown CPU"
        except Exception:
            pass

    return platform.processor() or f"Unknown ({platform.machine()})"
