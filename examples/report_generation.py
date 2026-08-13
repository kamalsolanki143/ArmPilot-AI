"""
ArmPilot-AI — Report Generation Example
Demonstrates generating reports from benchmark and optimization results.
"""

import json
from pathlib import Path

from app.schemas.benchmark import BenchmarkResult, LatencyMetrics, BenchmarkConfig
from app.schemas.optimization import OptimizationResult, OptimizationCandidate, OptimizationConfig
from app.reports.report_builder import generate_benchmark_report, generate_optimization_report


def create_sample_benchmark_result() -> BenchmarkResult:
    """Create a sample benchmark result for demonstration."""
    return BenchmarkResult(
        id="bench-demo-a1b2c3d4",
        status="completed",
        config=BenchmarkConfig(
            model="llama-3.2-1b-instruct",
            runtime="llama.cpp",
            quantization="INT8",
            batch_size=512,
            threads=4,
            concurrency=1,
            num_requests=10,
            max_tokens=128,
        ),
        timestamp="2026-08-13T12:00:00Z",
        ttft_ms=45.2,
        tokens_per_second=32.5,
        requests_per_second=0.8,
        total_tokens=1280,
        total_requests=10,
        latency=LatencyMetrics(
            p50_ms=1200.0,
            p75_ms=1350.0,
            p90_ms=1500.0,
            p95_ms=1600.0,
            p99_ms=1800.0,
            avg_ms=1250.0,
            min_ms=1100.0,
            max_ms=1900.0,
        ),
        cpu_utilization_percent=65.3,
        memory_mb=1024.5,
        memory_peak_mb=1200.0,
        model_size_mb=670.0,
        hardware={
            "architecture": "ARM64",
            "cpu_model": "Apple M2 Pro",
            "cpu_count": 10,
            "cpu_count_physical": 10,
            "memory_total_gb": 32.0,
            "is_arm64": True,
            "platform": "Darwin",
        },
        duration_seconds=120.5,
    )


def create_sample_optimization_result() -> OptimizationResult:
    """Create a sample optimization result for demonstration."""
    return OptimizationResult(
        id="opt-demo-e5f6g7h8",
        status="completed",
        config=OptimizationConfig(
            model="llama-3.2-1b-instruct",
            objective="throughput",
            quantization_options=["FP16", "INT8", "INT4"],
            batch_sizes=[1, 4, 8],
            thread_counts=[2, 4, 8],
        ),
        timestamp="2026-08-13T13:00:00Z",
        candidates=[
            OptimizationCandidate(
                id="c1", name="INT8-B4-T4", description="INT8, batch=4, threads=4",
                config={"quantization": "INT8", "batch_size": 4, "threads": 4},
                tokens_per_second=32.5, ttft_ms=45.2, memory_mb=1024.0, p95_latency_ms=1600.0,
                status="completed",
            ),
            OptimizationCandidate(
                id="c2", name="INT4-B8-T8", description="INT4, batch=8, threads=8",
                config={"quantization": "INT4", "batch_size": 8, "threads": 8},
                tokens_per_second=45.1, ttft_ms=32.0, memory_mb=512.0, p95_latency_ms=1200.0,
                status="completed",
            ),
            OptimizationCandidate(
                id="c3", name="FP16-B1-T2", description="FP16, batch=1, threads=2",
                config={"quantization": "FP16", "batch_size": 1, "threads": 2},
                tokens_per_second=18.3, ttft_ms=80.5, memory_mb=2048.0, p95_latency_ms=2400.0,
                status="completed",
            ),
        ],
        best_candidate=OptimizationCandidate(
            id="c2", name="INT4-B8-T8", description="INT4, batch=8, threads=8",
            config={"quantization": "INT4", "batch_size": 8, "threads": 8},
            tokens_per_second=45.1, ttft_ms=32.0, memory_mb=512.0, p95_latency_ms=1200.0,
            status="completed",
        ),
        improvement_summary={
            "tokens_per_second": {"before": 32.5, "after": 45.1, "change_percent": 38.8},
            "ttft_ms": {"before": 45.2, "after": 32.0, "change_percent": -29.2},
            "memory_mb": {"before": 1024.0, "after": 512.0, "change_percent": -50.0},
        },
        duration_seconds=300.0,
    )


def main() -> None:
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    # Benchmark report
    print("Generating benchmark report...")
    bench_result = create_sample_benchmark_result()
    bench_md = generate_benchmark_report(bench_result)

    bench_md_path = output_dir / "benchmark-report.md"
    bench_md_path.write_text(bench_md)
    print(f"  Markdown: {bench_md_path}")

    bench_json_path = output_dir / "benchmark-result.json"
    bench_json_path.write_text(bench_result.model_dump_json(indent=2))
    print(f"  JSON:     {bench_json_path}")

    print(f"\nBenchmark Report Preview (first 30 lines):\n")
    for line in bench_md.split("\n")[:30]:
        print(f"  {line}")
    print("  ...")

    # Optimization report
    print(f"\n{'='*60}\n")
    print("Generating optimization report...")
    opt_result = create_sample_optimization_result()
    opt_md = generate_optimization_report(opt_result)

    opt_md_path = output_dir / "optimization-report.md"
    opt_md_path.write_text(opt_md)
    print(f"  Markdown: {opt_md_path}")

    opt_json_path = output_dir / "optimization-result.json"
    opt_json_path.write_text(opt_result.model_dump_json(indent=2))
    print(f"  JSON:     {opt_json_path}")

    print(f"\nOptimization Report Preview (first 30 lines):\n")
    for line in opt_md.split("\n")[:30]:
        print(f"  {line}")
    print("  ...")

    # Summary
    print(f"\n{'='*60}")
    print(f"All reports saved to {output_dir}/")
    print(f"  - benchmark-report.md")
    print(f"  - benchmark-result.json")
    print(f"  - optimization-report.md")
    print(f"  - optimization-result.json")


if __name__ == "__main__":
    main()
