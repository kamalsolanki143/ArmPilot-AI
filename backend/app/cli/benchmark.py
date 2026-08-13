"""
ArmPilot-AI — Benchmark CLI Commands
"""

import asyncio

import click


@click.group()
def benchmark() -> None:
    """Run and manage inference benchmarks."""


@benchmark.command("run")
@click.option("--model", "-m", required=True, help="Model ID to benchmark.")
@click.option("--runtime", "-r", default="llama.cpp", help="Inference runtime.")
@click.option("--threads", "-t", default=4, type=int, help="Thread count.")
@click.option("--batch-size", "-b", default=512, type=int, help="Batch size.")
@click.option("--concurrency", "-c", default=1, type=int, help="Concurrent requests.")
@click.option("--num-requests", "-n", default=10, type=int, help="Total requests.")
@click.option("--max-tokens", default=128, type=int, help="Max tokens per response.")
@click.option("--warmup", default=3, type=int, help="Warmup requests.")
@click.option("--prompt", "-p", default=None, help="Custom prompt text.")
@click.option("--quantization", "-q", default=None, help="Quantization level (INT4, INT8, FP16).")
@click.option("--output", "-o", default=None, help="Save result JSON to file.")
def run_benchmark(
    model: str,
    runtime: str,
    threads: int,
    batch_size: int,
    concurrency: int,
    num_requests: int,
    max_tokens: int,
    warmup: int,
    prompt: str | None,
    quantization: str | None,
    output: str | None,
) -> None:
    """Run a benchmark against a model."""
    from app.core.logger import logger
    from app.schemas.benchmark import BenchmarkConfig

    config = BenchmarkConfig(
        model=model,
        runtime=runtime,
        quantization=quantization,
        batch_size=batch_size,
        threads=threads,
        concurrency=concurrency,
        num_requests=num_requests,
        max_tokens=max_tokens,
        warmup_requests=warmup,
        prompt=prompt or "Explain the benefits of ARM64 architecture for AI inference.",
    )

    click.echo(f"Starting benchmark for model '{model}'...")
    click.echo(f"  Runtime: {runtime}, Threads: {threads}, Batch: {batch_size}")
    click.echo(f"  Requests: {num_requests}, Concurrency: {concurrency}, Max tokens: {max_tokens}")
    click.echo()

    from app.benchmark.runner import benchmark_runner

    async def _run() -> None:
        result = await benchmark_runner.run(config)
        _print_result(result)
        if output:
            import json
            from pathlib import Path

            path = Path(output)
            path.write_text(result.model_dump_json(indent=2))
            click.echo(f"\nResult saved to {path}")

    try:
        asyncio.run(_run())
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@benchmark.command("compare")
@click.argument("result_a", type=click.Path(exists=True))
@click.argument("result_b", type=click.Path(exists=True))
def compare(result_a: str, result_b: str) -> None:
    """Compare two benchmark result JSON files."""
    import json
    from pathlib import Path

    a = json.loads(Path(result_a).read_text())
    b = json.loads(Path(result_b).read_text())

    click.echo("Benchmark Comparison")
    click.echo(f"  {'Metric':<25} {'A':>12} {'B':>12} {'Delta':>12}")
    click.echo(f"  {'─'*25} {'─'*12} {'─'*12} {'─'*12}")

    metrics = [
        ("tokens_per_second", "Tokens/sec"),
        ("ttft_ms", "TTFT (ms)"),
        ("total_tokens", "Total Tokens"),
        ("requests_per_second", "Req/sec"),
        ("duration_seconds", "Duration (s)"),
        ("cpu_utilization_percent", "CPU %"),
        ("memory_mb", "Memory (MB)"),
    ]

    for key, label in metrics:
        va = a.get(key)
        vb = b.get(key)
        if va is not None and vb is not None:
            delta = vb - va
            pct = (delta / va * 100) if va != 0 else 0
            click.echo(f"  {label:<25} {va:>12.1f} {vb:>12.1f} {pct:>+11.1f}%")
        else:
            click.echo(f"  {label:<25} {'N/A':>12} {'N/A':>12} {'N/A':>12}")

    # Latency
    la = a.get("latency", {})
    lb = b.get("latency", {})
    for pctl in ["p50_ms", "p90_ms", "p95_ms", "p99_ms"]:
        va = la.get(pctl)
        vb = lb.get(pctl)
        if va is not None and vb is not None:
            delta = vb - va
            pct = (delta / va * 100) if va != 0 else 0
            click.echo(f"  {pctl.upper():<25} {va:>12.1f} {vb:>12.1f} {pct:>+11.1f}%")


@benchmark.command("list")
def list_benchmarks() -> None:
    """List saved benchmark results."""
    from app.core.config import settings
    from pathlib import Path
    import json

    reports_dir = settings.resolve_path(settings.reports_dir)
    if not reports_dir.exists():
        click.echo("No reports directory found.")
        return

    results = sorted(reports_dir.glob("bench-*.json"))
    if not results:
        click.echo("No saved benchmarks found.")
        return

    click.echo(f"Found {len(results)} benchmark result(s):\n")
    click.echo(f"  {'File':<40} {'Model':<20} {'TPS':<10} {'TTFT':<10} {'Status'}")
    click.echo(f"  {'─'*40} {'─'*20} {'─'*10} {'─'*10} {'─'*10}")

    for fp in results:
        try:
            data = json.loads(fp.read_text())
            model = data.get("config", {}).get("model", "?")
            tps = data.get("tokens_per_second", 0)
            ttft = data.get("ttft_ms", 0)
            status = data.get("status", "?")
            click.echo(f"  {fp.name:<40} {model:<20} {tps:<10.1f} {ttft:<10.1f} {status}")
        except Exception:
            click.echo(f"  {fp.name:<40} {'(parse error)':<20}")


def _print_result(result) -> None:
    """Pretty-print a BenchmarkResult."""
    click.echo(f"\n{'='*60}")
    click.echo(f"Benchmark: {result.id}")
    click.echo(f"Status: {result.status}")
    click.echo(f"{'='*60}")

    if result.status == "failed":
        click.echo(f"Error: {result.error}")
        return

    click.echo(f"\n  {'Metric':<25} {'Value':>12}")
    click.echo(f"  {'─'*25} {'─'*12}")
    click.echo(f"  {'Tokens/sec':<25} {result.tokens_per_second:>12.1f}")
    click.echo(f"  {'TTFT':<25} {result.ttft_ms:>10.1f} ms")
    click.echo(f"  {'Requests/sec':<25} {result.requests_per_second:>12.1f}")
    click.echo(f"  {'Total Tokens':<25} {result.total_tokens:>12}")
    click.echo(f"  {'Total Requests':<25} {result.total_requests:>12}")
    click.echo(f"  {'Duration':<25} {result.duration_seconds:>10.1f} s")
    click.echo()

    lat = result.latency
    click.echo("  Latency:")
    click.echo(f"    P50={lat.p50_ms:.1f}ms  P90={lat.p90_ms:.1f}ms  P95={lat.p95_ms:.1f}ms  P99={lat.p99_ms:.1f}ms")
    click.echo()

    click.echo("  Resources:")
    click.echo(f"    CPU: {result.cpu_utilization_percent:.1f}%")
    click.echo(f"    Memory: {result.memory_mb:.1f} MB")
    if result.model_size_mb:
        click.echo(f"    Model size: {result.model_size_mb:.0f} MB")
