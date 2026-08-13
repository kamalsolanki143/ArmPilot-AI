"""
ArmPilot-AI — Optimization CLI Commands
"""

import asyncio

import click


@click.group()
def optimize() -> None:
    """Run and manage model optimization sweeps."""


@optimize.command("run")
@click.option("--model", "-m", required=True, help="Model ID to optimize.")
@click.option(
    "--objective", "-o",
    default="throughput",
    type=click.Choice(["throughput", "latency", "memory", "balanced"]),
    help="Optimization objective.",
)
@click.option("--quantization", "-q", multiple=True, default=["INT8", "INT4"], help="Quantization options.")
@click.option("--batch-sizes", "-b", multiple=True, type=int, default=[1, 4, 8], help="Batch sizes to try.")
@click.option("--threads", "-t", multiple=True, type=int, default=[2, 4, 8], help="Thread counts to try.")
@click.option("--max-candidates", default=8, type=int, help="Max configurations to test.")
@click.option("--benchmarks-per", default=5, type=int, help="Benchmarks per candidate.")
@click.option("--max-tokens", default=128, type=int, help="Max tokens per benchmark request.")
@click.option("--output", default=None, help="Save result JSON to file.")
def run_optimize(
    model: str,
    objective: str,
    quantization: tuple[str, ...],
    batch_sizes: tuple[int, ...],
    threads: tuple[int, ...],
    max_candidates: int,
    benchmarks_per: int,
    max_tokens: int,
    output: str | None,
) -> None:
    """Run an optimization sweep to find the best configuration."""
    from app.schemas.optimization import OptimizationConfig

    config = OptimizationConfig(
        model=model,
        objective=objective,
        quantization_options=list(quantization),
        batch_sizes=list(batch_sizes),
        thread_counts=list(threads),
        max_candidates=max_candidates,
        benchmark_per_candidate=benchmarks_per,
        max_tokens=max_tokens,
    )

    click.echo(f"Starting optimization for model '{model}'...")
    click.echo(f"  Objective: {objective}")
    click.echo(f"  Quantizations: {list(quantization)}")
    click.echo(f"  Batch sizes: {list(batch_sizes)}")
    click.echo(f"  Thread counts: {list(threads)}")
    click.echo(f"  Max candidates: {max_candidates}")
    click.echo()

    async def _run() -> None:
        # Build candidate list from parameter space
        candidates = _generate_candidates(config)
        click.echo(f"Generated {len(candidates)} candidate configurations.\n")

        # Run benchmarks for each candidate
        from app.benchmark.runner import benchmark_runner
        from app.schemas.benchmark import BenchmarkConfig

        results = []
        for i, candidate in enumerate(candidates, 1):
            click.echo(f"[{i}/{len(candidates)}] Testing: {candidate.name}...")
            bc = candidate.config

            bench_config = BenchmarkConfig(
                model=model,
                batch_size=bc.get("batch_size", 512),
                threads=bc.get("threads", 4),
                num_requests=benchmarks_per,
                max_tokens=max_tokens,
                prompt="Explain the benefits of ARM64 architecture for AI inference.",
            )

            try:
                result = await benchmark_runner.run(bench_config)
                candidate.tokens_per_second = result.tokens_per_second
                candidate.ttft_ms = result.ttft_ms
                candidate.memory_mb = result.memory_mb
                candidate.p95_latency_ms = result.latency.p95_ms
                candidate.status = "completed"
                results.append(candidate)
                click.echo(
                    f"  -> TPS={result.tokens_per_second:.1f}, "
                    f"TTFT={result.ttft_ms:.1f}ms, "
                    f"P95={result.latency.p95_ms:.1f}ms"
                )
            except Exception as e:
                candidate.status = "failed"
                click.echo(f"  -> Failed: {e}")

        # Find best
        if results:
            best = max(results, key=lambda c: c.tokens_per_second or 0)
            click.echo(f"\n{'='*60}")
            click.echo(f"Best configuration: {best.name}")
            click.echo(f"  Tokens/sec: {best.tokens_per_second:.1f}")
            click.echo(f"  TTFT: {best.ttft_ms:.1f}ms")
            click.echo(f"  P95 Latency: {best.p95_latency_ms:.1f}ms")
            click.echo(f"  Memory: {best.memory_mb:.1f} MB")
            click.echo(f"{'='*60}")

            if output:
                import json
                from pathlib import Path
                data = {
                    "best": best.model_dump(),
                    "all": [c.model_dump() for c in results],
                }
                Path(output).write_text(json.dumps(data, indent=2))
                click.echo(f"\nResults saved to {output}")

    try:
        asyncio.run(_run())
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


def _generate_candidates(config):
    """Generate optimization candidates from parameter space."""
    from app.schemas.optimization import OptimizationCandidate
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


@optimize.command("status")
def opt_status() -> None:
    """Show optimization service status."""
    click.echo("Optimization Service")
    click.echo("  Available commands: run, status")
    click.echo("  Objectives: throughput, latency, memory, balanced")
