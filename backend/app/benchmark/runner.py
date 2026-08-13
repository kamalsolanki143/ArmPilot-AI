"""
ArmPilot-AI — Benchmark Runner
Orchestrates concurrent benchmark runs with configurable concurrency control.
"""

from __future__ import annotations

import asyncio
import statistics
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.logger import logger
from app.schemas.benchmark import BenchmarkConfig, BenchmarkResult, LatencyMetrics
from app.utils.hardware import get_hardware_info, get_system_metrics, get_process_metrics
from app.services.inference_service import inference_service


class BenchmarkRunner:
    """Runs inference benchmarks and collects metrics with concurrent execution."""

    def __init__(self) -> None:
        self._running = False
        self._current_id: str | None = None
        self._active_benchmarks: dict[str, asyncio.Task[BenchmarkResult]] = {}

    @property
    def is_running(self) -> bool:
        return self._running

    async def run(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Execute a full benchmark run with concurrent request execution."""
        if self._running:
            raise RuntimeError("A benchmark is already running")

        benchmark_id = f"bench-{uuid.uuid4().hex[:8]}"
        self._running = True
        self._current_id = benchmark_id

        result = BenchmarkResult(
            id=benchmark_id,
            status="running",
            config=config,
            timestamp=datetime.now(timezone.utc).isoformat(),
            hardware=get_hardware_info(),
        )

        logger.info(
            "Benchmark %s starting — model=%s, requests=%d, concurrency=%d",
            benchmark_id, config.model, config.num_requests, config.concurrency,
        )

        try:
            # Ensure model is loaded
            if not inference_service.runtime or not inference_service.runtime.is_loaded():
                inference_service.load_model(
                    config.model,
                    n_threads=config.threads,
                    n_batch=config.batch_size,
                )

            # Warmup phase
            if config.warmup_requests > 0:
                logger.info("Warmup: %d requests", config.warmup_requests)
                warmup_sem = asyncio.Semaphore(min(config.concurrency, config.warmup_requests))
                warmup_tasks = [
                    self._single_request(config, warmup_sem)
                    for _ in range(config.warmup_requests)
                ]
                await asyncio.gather(*warmup_tasks)

            # Concurrent benchmark execution
            bench_start = time.perf_counter()
            start_metrics = get_system_metrics()

            sem = asyncio.Semaphore(config.concurrency)
            tasks = [
                self._single_request(config, sem)
                for _ in range(config.num_requests)
            ]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

            bench_duration = time.perf_counter() - bench_start
            end_metrics = get_system_metrics()
            proc_metrics = get_process_metrics()

            # Aggregate results
            latencies_ms: list[float] = []
            ttfts_ms: list[float] = []
            total_tokens = 0
            errors = 0

            for i, res in enumerate(raw_results):
                if isinstance(res, Exception):
                    errors += 1
                    logger.warning("Benchmark request %d failed: %s", i + 1, res)
                else:
                    latencies_ms.append(res["latency_ms"])
                    if res.get("ttft_ms"):
                        ttfts_ms.append(res["ttft_ms"])
                    total_tokens += res.get("completion_tokens", 0)

            # Compute latency percentiles
            latency = LatencyMetrics()
            if latencies_ms:
                sorted_lat = sorted(latencies_ms)
                latency.avg_ms = round(statistics.mean(sorted_lat), 2)
                latency.min_ms = round(sorted_lat[0], 2)
                latency.max_ms = round(sorted_lat[-1], 2)
                latency.p50_ms = round(self._percentile(sorted_lat, 50), 2)
                latency.p75_ms = round(self._percentile(sorted_lat, 75), 2)
                latency.p90_ms = round(self._percentile(sorted_lat, 90), 2)
                latency.p95_ms = round(self._percentile(sorted_lat, 95), 2)
                latency.p99_ms = round(self._percentile(sorted_lat, 99), 2)

            avg_ttft = round(statistics.mean(ttfts_ms), 2) if ttfts_ms else None

            # Throughput metrics
            successful = config.num_requests - errors
            tps = round(total_tokens / bench_duration, 2) if bench_duration > 0 else 0
            rps = round(successful / bench_duration, 2) if bench_duration > 0 else 0

            # Populate result
            result.status = "completed"
            result.ttft_ms = avg_ttft
            result.tokens_per_second = tps
            result.requests_per_second = rps
            result.total_tokens = total_tokens
            result.total_requests = successful
            result.latency = latency
            result.cpu_utilization_percent = round(
                (start_metrics["cpu_utilization_percent"] + end_metrics["cpu_utilization_percent"]) / 2, 1
            )
            result.memory_mb = round(proc_metrics.get("memory_rss_mb", 0), 1)
            result.memory_peak_mb = round(end_metrics.get("memory_used_mb", 0), 1)
            result.duration_seconds = round(bench_duration, 2)

            if inference_service.runtime and inference_service.runtime.is_loaded():
                info = inference_service.runtime.get_model_info()
                result.model_size_mb = info.get("file_size_mb")

            logger.info(
                "Benchmark %s completed — TPS=%.1f, TTFT=%.1fms, P95=%.1fms, Duration=%.1fs, Concurrency=%d",
                benchmark_id, tps, avg_ttft or 0, latency.p95_ms, bench_duration, config.concurrency,
            )

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            logger.error("Benchmark %s failed: %s", benchmark_id, e)

        finally:
            self._running = False
            self._current_id = None

        return result

    async def _single_request(self, config: BenchmarkConfig, sem: asyncio.Semaphore) -> dict[str, Any]:
        """Execute a single inference request with semaphore-based concurrency control."""
        async with sem:
            start = time.perf_counter()

            # Stream to measure TTFT
            ttft_ms = None
            token_count = 0

            stream = inference_service.runtime.generate_stream(
                prompt=config.prompt,
                max_tokens=config.max_tokens,
                temperature=0.7,
            )

            for chunk in stream:
                token_count += 1
                if chunk.get("is_first") and "ttft_ms" in chunk:
                    ttft_ms = chunk["ttft_ms"]

            latency_ms = (time.perf_counter() - start) * 1000

            return {
                "latency_ms": latency_ms,
                "ttft_ms": ttft_ms,
                "completion_tokens": token_count,
            }

    @staticmethod
    def _percentile(sorted_data: list[float], p: float) -> float:
        """Compute the p-th percentile of sorted data."""
        if not sorted_data:
            return 0.0
        k = (len(sorted_data) - 1) * (p / 100)
        f = int(k)
        c = f + 1
        if c >= len(sorted_data):
            return sorted_data[-1]
        d0 = sorted_data[f] * (c - k)
        d1 = sorted_data[c] * (k - f)
        return d0 + d1


# Singleton
benchmark_runner = BenchmarkRunner()
