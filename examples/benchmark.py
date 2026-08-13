"""
ArmPilot-AI — Benchmark Example
Demonstrates how to programmatically run a benchmark and inspect results.
"""

import asyncio
import json

from app.schemas.benchmark import BenchmarkConfig
from app.benchmark.runner import benchmark_runner
from app.reports.report_builder import generate_benchmark_report


async def main() -> None:
    # Configure the benchmark
    config = BenchmarkConfig(
        model="llama-3.2-1b-instruct",
        runtime="llama.cpp",
        threads=4,
        batch_size=512,
        concurrency=1,
        num_requests=5,
        max_tokens=128,
        warmup_requests=2,
        prompt="Explain the benefits of ARM64 architecture for AI inference.",
    )

    print(f"Running benchmark for model: {config.model}")
    print(f"  Threads: {config.threads}, Batch: {config.batch_size}")
    print(f"  Requests: {config.num_requests}, Concurrency: {config.concurrency}")
    print()

    # Run the benchmark
    result = await benchmark_runner.run(config)

    # Print results
    print(f"Benchmark ID: {result.id}")
    print(f"Status: {result.status}")

    if result.status == "completed":
        print(f"\nResults:")
        print(f"  Tokens/sec:     {result.tokens_per_second:.1f}")
        print(f"  TTFT:           {result.ttft_ms:.1f} ms")
        print(f"  Requests/sec:   {result.requests_per_second:.1f}")
        print(f"  Total tokens:   {result.total_tokens}")
        print(f"  Duration:       {result.duration_seconds:.1f} s")
        print(f"\n  Latency:")
        print(f"    P50={result.latency.p50_ms:.1f}ms  P90={result.latency.p90_ms:.1f}ms  "
              f"P95={result.latency.p95_ms:.1f}ms  P99={result.latency.p99_ms:.1f}ms")
        print(f"\n  Resources:")
        print(f"    CPU: {result.cpu_utilization_percent:.1f}%")
        print(f"    Memory: {result.memory_mb:.1f} MB")

        # Generate a report
        report_md = generate_benchmark_report(result)
        print(f"\n{'='*60}")
        print(report_md)

        # Save the result
        output_path = f"reports/{result.id}.json"
        print(f"\nResult saved to {output_path}")
    else:
        print(f"Benchmark failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
