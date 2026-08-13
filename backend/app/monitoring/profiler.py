"""
ArmPilot-AI — Performance Profiler
Profiles function execution times, memory allocations, and inference hotspots.
"""

from __future__ import annotations

import cProfile
import functools
import io
import pstats
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Optional, TypeVar

from app.core.logger import logger

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class ProfileResult:
    """Result of a profiling session."""
    name: str
    total_time: float
    call_count: int
    avg_time: float
    min_time: float
    max_time: float
    calls: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "total_time_s": round(self.total_time, 4),
            "call_count": self.call_count,
            "avg_time_s": round(self.avg_time, 6),
            "min_time_s": round(self.min_time, 6),
            "max_time_s": round(self.max_time, 6),
        }


@dataclass
class _CallRecord:
    elapsed: float
    timestamp: float
    success: bool
    error: Optional[str] = None


class PerformanceProfiler:
    """Tracks per-function profiling data across the application."""

    def __init__(self) -> None:
        self._records: dict[str, list[_CallRecord]] = defaultdict(list)
        self._cprofile: Optional[cProfile.Profile] = None
        self._enabled = True
        self._max_records_per_func = 1000

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def record_call(
        self,
        name: str,
        elapsed: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Manually record a function call."""
        if not self._enabled:
            return
        records = self._records[name]
        if len(records) < self._max_records_per_func:
            records.append(_CallRecord(
                elapsed=elapsed,
                timestamp=time.time(),
                success=success,
                error=error,
            ))

    def get_profile(self, name: str) -> Optional[ProfileResult]:
        """Get profiling data for a named function."""
        records = self._records.get(name)
        if not records:
            return None

        times = [r.elapsed for r in records]
        return ProfileResult(
            name=name,
            total_time=sum(times),
            call_count=len(times),
            avg_time=sum(times) / len(times),
            min_time=min(times),
            max_time=max(times),
        )

    def get_all_profiles(self) -> list[ProfileResult]:
        """Get profiling data for all tracked functions."""
        results = []
        for name in sorted(self._records):
            profile = self.get_profile(name)
            if profile:
                results.append(profile)
        return sorted(results, key=lambda p: p.total_time, reverse=True)

    def get_slowest(self, top_n: int = 10) -> list[ProfileResult]:
        """Return the N slowest functions by total time."""
        return self.get_all_profiles()[:top_n]

    def get_error_rate(self, name: str) -> float:
        """Get error rate for a function (0.0 to 1.0)."""
        records = self._records.get(name, [])
        if not records:
            return 0.0
        errors = sum(1 for r in records if not r.success)
        return errors / len(records)

    def clear(self) -> None:
        """Clear all profiling data."""
        self._records.clear()

    def summary(self) -> dict[str, Any]:
        """Return a summary of all profiling data."""
        profiles = self.get_all_profiles()
        return {
            "total_functions": len(profiles),
            "total_calls": sum(p.call_count for p in profiles),
            "total_time_s": round(sum(p.total_time for p in profiles), 4),
            "slowest": [p.to_dict() for p in profiles[:10]],
            "error_rates": {
                p.name: round(self.get_error_rate(p.name), 4)
                for p in profiles
                if self.get_error_rate(p.name) > 0
            },
        }

    # ── cProfile integration ─────────────────────────────────────────

    def start_cprofile(self) -> None:
        """Start a cProfile session for CPU profiling."""
        self._cprofile = cProfile.Profile()
        self._cprofile.enable()
        logger.info("cProfile started")

    def stop_cprofile(self) -> Optional[dict[str, Any]]:
        """Stop cProfile and return top functions by cumulative time."""
        if self._cprofile is None:
            return None
        self._cprofile.disable()

        stream = io.StringIO()
        stats = pstats.Stats(self._cprofile, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)

        result = {"output": stream.getvalue()}
        self._cprofile = None
        logger.info("cProfile stopped")
        return result


# ── Decorator and context manager ───────────────────────────────────────

profiler = PerformanceProfiler()


def profile(
    name: Optional[str] = None,
    *,
    log_slow_threshold: float = 1.0,
) -> Callable[[F], F]:
    """Decorator that profiles function execution time.

    Args:
        name: Custom name for the profile entry. Defaults to the function's qualified name.
        log_slow_threshold: Log a warning if execution exceeds this many seconds.
    """

    def decorator(func: F) -> F:
        profile_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            success = True
            error_msg = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as exc:
                success = False
                error_msg = str(exc)
                raise
            finally:
                elapsed = time.perf_counter() - start
                profiler.record_call(profile_name, elapsed, success, error_msg)
                if elapsed > log_slow_threshold:
                    logger.warning("Slow call %s: %.3fs", profile_name, elapsed)

        return wrapper  # type: ignore[return-value]

    return decorator


@contextmanager
def profile_block(name: str) -> Generator[None, None, None]:
    """Context manager to profile a block of code."""
    start = time.perf_counter()
    success = True
    error_msg = None
    try:
        yield
    except Exception as exc:
        success = False
        error_msg = str(exc)
        raise
    finally:
        elapsed = time.perf_counter() - start
        profiler.record_call(name, elapsed, success, error_msg)
        logger.debug("Profile %s: %.4fs", name, elapsed)


def profile_inference(model: str = "unknown") -> Callable[[F], F]:
    """Specialized decorator for profiling inference calls with model tagging."""

    def decorator(func: F) -> F:
        profile_name = f"inference.{model}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            success = True
            error_msg = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as exc:
                success = False
                error_msg = str(exc)
                raise
            finally:
                elapsed = time.perf_counter() - start
                profiler.record_call(profile_name, elapsed, success, error_msg)
                if elapsed > 2.0:
                    logger.warning("Slow inference %s: %.3fs", model, elapsed)

        return wrapper  # type: ignore[return-value]

    return decorator
