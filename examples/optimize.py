"""
ArmPilot-AI — Optimization Example
Demonstrates running an optimization sweep to find the best model configuration.
"""

import asyncio

from app.schemas.optimization import OptimizationConfig, OptimizationCandidate
from app.schemas.benchmark import BenchmarkConfig
from app.benchmark.runner import benchmark_runner


def generate_candidates(config: OptimizationConfig) -> list[OptimizationCandidate]:
    """Generate candidate configurations from the parameter space."""
    import uuid
    candidates = []
    for quant in config.quantization_options:
        for batch in config.batch_sizes:
            for thread in config.thread_counts:
                if len(candidates) >= config.max_candidates:
                    return candidates
                candidates.append(OptimizationCandidate(
                    id=f"opt-{uuid.uuid4().hex[:6]}",
                    name=f"{quant}-B{batch}-T{thread}",
                    description=f"Quantization={quant}, Batch={batch}, Threads={thread}",
                    config={"quantization": quant, "batch_size": batch, "threads": thread},
                ))
    return candidates


async def main() -> None:
    config = OptimizationConfig(
        model="llama-3.2-1b-instruct",
        objective="throughput",
        quantization_options=["INT8", "INT4"],
        batch_sizes=[1, 4, 8],
        thread_counts=[2, 4],
        max_candidates=6,
        benchmark_per_candidate=3,
        max_tokens=128,
    )

    print(f"Optimization sweep for model: {config.model}")
    print(f"Objective: {config.objective}")
    print(f"  Quantizations: {config.quantization_options}")
    print(f"  Batch sizes: {config.batch_sizes}")
    print(f"  Thread counts: {config.thread_counts}")
    print()

    candidates = generate_candidates(config)
    print(f"Generated {len(candidates)} candidate configurations.\n")

    # Run benchmarks for each candidate
    results = []
    for i, candidate in enumerate(candidates, 1):
        cc = candidate.config
        print(f"[{i}/{len(candidates)}] Testing: {candidate.name}")

        bench_config = BenchmarkConfig(
            model=config.model,
            batch_size=cc["batch_size"],
            threads=cc["threads"],
            num_requests=config.benchmark_per_candidate,
            max_tokens=config.max_tokens,
        )

        try:
            result = await benchmark_runner.run(bench_config)
            candidate.tokens_per_second = result.tokens_per_second
            candidate.ttft_ms = result.ttft_ms
            candidate.memory_mb = result.memory_mb
            candidate.p95_latency_ms = result.latency.p95_ms
            candidate.status = "completed"
            results.append(candidate)
            print(f"  -> TPS={result.tokens_per_second:.1f}, "
                  f"TTFT={result.ttft_ms:.1f}ms, "
                  f"P95={result.latency.p95_ms:.1f}ms, "
                  f"Memory={result.memory_mb:.1f}MB\n")
        except Exception as e:
            candidate.status = "failed"
            print(f"  -> Failed: {e}\n")

    # Report results
    if not results:
        print("No successful benchmarks. Check model availability.")
        return

    print("=" * 70)
    print("Optimization Results")
    print("=" * 70)
    print(f"\n  {'Name':<25} {'TPS':>8} {'TTFT':>10} {'P95':>10} {'Memory':>10}")
    print(f"  {'─'*25} {'─'*8} {'─'*10} {'─'*10} {'─'*10}")
    for c in results:
        print(f"  {c.name:<25} {c.tokens_per_second:>8.1f} "
              f"{c.ttft_ms:>8.1f}ms {c.p95_latency_ms:>8.1f}ms "
              f"{c.memory_mb:>8.1f}MB")

    best = max(results, key=lambda c: c.tokens_per_second or 0)
    print(f"\nBest configuration: {best.name}")
    print(f"  Tokens/sec: {best.tokens_per_second:.1f}")
    print(f"  TTFT: {best.ttft_ms:.1f}ms")
    print(f"  P95 Latency: {best.p95_latency_ms:.1f}ms")
    print(f"  Memory: {best.memory_mb:.1f} MB")
    print()

    # Save results
    import json
    from pathlib import Path

    output = Path("reports") / f"optimization-{best.id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "best": best.model_dump(),
        "all": [c.model_dump() for c in results],
    }
    output.write_text(json.dumps(data, indent=2))
    print(f"Results saved to {output}")


if __name__ == "__main__":
    asyncio.run(main())
