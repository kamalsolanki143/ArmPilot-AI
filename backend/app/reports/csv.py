"""
ArmPilot-AI — CSV Report Generator
Exports benchmark and optimization results as CSV data.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from app.schemas.benchmark import BenchmarkResult, LatencyMetrics
from app.schemas.optimization import OptimizationResult, OptimizationCandidate


def generate_benchmark_csv(result: BenchmarkResult) -> str:
    """Generate a CSV report for a benchmark run.

    Produces a two-section CSV:
      1. Summary row with key metrics
      2. Latency percentiles
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Section 1: Summary
    writer.writerow(["=== Benchmark Summary ==="])
    writer.writerow(["Field", "Value"])
    writer.writerow(["Report ID", result.id])
    writer.writerow(["Status", result.status])
    writer.writerow(["Timestamp", result.timestamp or ""])
    writer.writerow(["Model", result.config.model])
    writer.writerow(["Runtime", result.config.runtime])
    writer.writerow(["Quantization", result.config.quantization or "Default"])
    writer.writerow(["Batch Size", result.config.batch_size])
    writer.writerow(["Threads", result.config.threads])
    writer.writerow(["Concurrency", result.config.concurrency])
    writer.writerow(["Num Requests", result.config.num_requests])
    writer.writerow(["Max Tokens", result.config.max_tokens])
    writer.writerow(["TTFT (ms)", result.ttft_ms or ""])
    writer.writerow(["Tokens/sec", result.tokens_per_second or ""])
    writer.writerow(["Requests/sec", result.requests_per_second or ""])
    writer.writerow(["Total Tokens", result.total_tokens])
    writer.writerow(["Total Requests", result.total_requests])
    writer.writerow(["Duration (s)", result.duration_seconds or ""])
    writer.writerow(["CPU Utilization (%)", result.cpu_utilization_percent or ""])
    writer.writerow(["Memory (MB)", result.memory_mb or ""])
    writer.writerow(["Memory Peak (MB)", result.memory_peak_mb or ""])
    writer.writerow(["Model Size (MB)", result.model_size_mb or ""])
    writer.writerow([])

    # Section 2: Latency
    writer.writerow(["=== Latency Distribution ==="])
    writer.writerow(["Percentile", "Value (ms)"])
    lat = result.latency
    for label, value in [
        ("P50", lat.p50_ms),
        ("P75", lat.p75_ms),
        ("P90", lat.p90_ms),
        ("P95", lat.p95_ms),
        ("P99", lat.p99_ms),
        ("Avg", lat.avg_ms),
        ("Min", lat.min_ms),
        ("Max", lat.max_ms),
    ]:
        writer.writerow([label, value])

    return output.getvalue()


def generate_optimization_csv(result: OptimizationResult) -> str:
    """Generate a CSV report for an optimization run."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["=== Optimization Summary ==="])
    writer.writerow(["Field", "Value"])
    writer.writerow(["Report ID", result.id])
    writer.writerow(["Status", result.status])
    writer.writerow(["Timestamp", result.timestamp or ""])
    writer.writerow(["Model", result.config.model])
    writer.writerow(["Objective", result.config.objective])
    writer.writerow(["Duration (s)", result.duration_seconds or ""])
    writer.writerow([])

    # Baseline
    if result.baseline:
        writer.writerow(["=== Baseline ==="])
        writer.writerow(["Metric", "Value"])
        for k, v in result.baseline.items():
            if k != "benchmark_id":
                writer.writerow([k, v])
        writer.writerow([])

    # Improvement summary
    if result.improvement_summary:
        writer.writerow(["=== Improvements ==="])
        writer.writerow(["Metric", "Before", "After", "Change (%)"])
        for metric, data in result.improvement_summary.items():
            if isinstance(data, dict):
                writer.writerow([
                    metric,
                    data.get("before", ""),
                    data.get("after", ""),
                    f"{data.get('change_percent', 0):+.1f}",
                ])
        writer.writerow([])

    # Candidates
    if result.candidates:
        writer.writerow(["=== All Candidates ==="])
        writer.writerow(["Name", "Description", "Tokens/sec", "TTFT (ms)", "P95 (ms)", "Memory (MB)", "Status"])
        for c in result.candidates:
            writer.writerow([
                c.name,
                c.description,
                c.tokens_per_second or "",
                c.ttft_ms or "",
                c.p95_latency_ms or "",
                c.memory_mb or "",
                c.status,
            ])

        # Best candidate highlight
        if result.best_candidate:
            writer.writerow([])
            writer.writerow(["=== Best Candidate ==="])
            bc = result.best_candidate
            writer.writerow(["Name", bc.name])
            writer.writerow(["Tokens/sec", bc.tokens_per_second or ""])
            writer.writerow(["TTFT (ms)", bc.ttft_ms or ""])
            writer.writerow(["P95 Latency (ms)", bc.p95_latency_ms or ""])
            writer.writerow(["Memory (MB)", bc.memory_mb or ""])

    return output.getvalue()


def generate_candidates_csv(candidates: list[OptimizationCandidate]) -> str:
    """Generate a simple CSV comparing optimization candidates."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Description", "Tokens/sec", "TTFT (ms)", "P95 (ms)", "Memory (MB)", "Status"])
    for c in candidates:
        writer.writerow([
            c.name,
            c.description,
            c.tokens_per_second or "",
            c.ttft_ms or "",
            c.p95_latency_ms or "",
            c.memory_mb or "",
            c.status,
        ])
    return output.getvalue()


def generate_latency_csv(latency: LatencyMetrics) -> str:
    """Generate a simple two-column CSV of latency percentiles."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Percentile", "Value (ms)"])
    for label, value in [
        ("P50", latency.p50_ms),
        ("P75", latency.p75_ms),
        ("P90", latency.p90_ms),
        ("P95", latency.p95_ms),
        ("P99", latency.p99_ms),
        ("Avg", latency.avg_ms),
        ("Min", latency.min_ms),
        ("Max", latency.max_ms),
    ]:
        writer.writerow([label, value])
    return output.getvalue()
