"""
ArmPilot-AI — Report CLI Commands
"""

import click


@click.group()
def report() -> None:
    """Generate and export benchmark/optimization reports."""


@report.command("generate")
@click.option("--benchmark-id", "-b", default=None, help="Benchmark ID to report on.")
@click.option("--optimization-id", "-o", default=None, help="Optimization ID to report on.")
@click.option(
    "--format", "-f",
    "fmt",
    default="markdown",
    type=click.Choice(["markdown", "html", "json", "csv"]),
    help="Output format.",
)
@click.option("--output", default=None, help="Output file path.")
@click.option("--no-charts", is_flag=True, help="Exclude charts from report.")
@click.option("--no-hardware", is_flag=True, help="Exclude hardware section.")
def generate_report(
    benchmark_id: str | None,
    optimization_id: str | None,
    fmt: str,
    output: str | None,
    no_charts: bool,
    no_hardware: bool,
) -> None:
    """Generate a report from benchmark or optimization results."""
    from app.core.config import settings
    from pathlib import Path
    import json

    if not benchmark_id and not optimization_id:
        click.echo("Error: provide --benchmark-id or --optimization-id.", err=True)
        raise SystemExit(1)

    reports_dir = settings.resolve_path(settings.reports_dir)

    if benchmark_id:
        result_path = reports_dir / f"{benchmark_id}.json"
        if not result_path.exists():
            click.echo(f"Error: benchmark result not found at {result_path}", err=True)
            raise SystemExit(1)

        data = json.loads(result_path.read_text())

        if fmt == "json":
            content = json.dumps(data, indent=2)
        elif fmt == "markdown":
            from app.schemas.benchmark import BenchmarkResult
            from app.reports.report_builder import generate_benchmark_report
            result = BenchmarkResult(**data)
            content = generate_benchmark_report(result)
        elif fmt == "csv":
            content = _benchmark_to_csv(data)
        elif fmt == "html":
            content = _benchmark_to_html(data)
        else:
            content = json.dumps(data, indent=2)

    elif optimization_id:
        result_path = reports_dir / f"{optimization_id}.json"
        if not result_path.exists():
            click.echo(f"Error: optimization result not found at {result_path}", err=True)
            raise SystemExit(1)

        data = json.loads(result_path.read_text())

        if fmt == "json":
            content = json.dumps(data, indent=2)
        elif fmt == "markdown":
            from app.schemas.optimization import OptimizationResult
            from app.reports.report_builder import generate_optimization_report
            result = OptimizationResult(**data)
            content = generate_optimization_report(result)
        elif fmt == "csv":
            content = _optimization_to_csv(data)
        elif fmt == "html":
            content = _optimization_to_html(data)
        else:
            content = json.dumps(data, indent=2)

    if output:
        from pathlib import Path
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content)
        click.echo(f"Report saved to {out_path}")
    else:
        click.echo(content)


@report.command("list")
def list_reports() -> None:
    """List all saved reports and results."""
    from app.core.config import settings
    from pathlib import Path

    reports_dir = settings.resolve_path(settings.reports_dir)
    if not reports_dir.exists():
        click.echo("No reports directory found.")
        return

    files = sorted(reports_dir.glob("*.*"))
    if not files:
        click.echo("No reports found.")
        return

    click.echo(f"Reports in {reports_dir}:\n")
    for fp in files:
        size_kb = fp.stat().st_size / 1024
        click.echo(f"  {fp.name:<45} {size_kb:>8.1f} KB")


@report.command("export")
@click.argument("benchmark_id")
@click.option(
    "--format", "-f",
    "fmt",
    default="markdown",
    type=click.Choice(["markdown", "html", "json", "csv"]),
    help="Export format.",
)
@click.option("--output", "-o", required=True, help="Output file path.")
def export_report(benchmark_id: str, fmt: str, output: str) -> None:
    """Export a benchmark report to a specific file."""
    from app.core.config import settings
    from pathlib import Path
    import json

    reports_dir = settings.resolve_path(settings.reports_dir)
    result_path = reports_dir / f"{benchmark_id}.json"
    if not result_path.exists():
        click.echo(f"Error: result not found at {result_path}", err=True)
        raise SystemExit(1)

    data = json.loads(result_path.read_text())

    if fmt == "json":
        content = json.dumps(data, indent=2)
    elif fmt == "markdown":
        from app.schemas.benchmark import BenchmarkResult
        from app.reports.report_builder import generate_benchmark_report
        result = BenchmarkResult(**data)
        content = generate_benchmark_report(result)
    elif fmt == "csv":
        content = _benchmark_to_csv(data)
    elif fmt == "html":
        content = _benchmark_to_html(data)
    else:
        content = json.dumps(data, indent=2)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content)
    click.echo(f"Exported to {out_path}")


def _benchmark_to_csv(data: dict) -> str:
    """Convert benchmark data to CSV."""
    lines = ["metric,value"]
    lines.append(f"id,{data.get('id', '')}")
    lines.append(f"status,{data.get('status', '')}")
    lines.append(f"model,{data.get('config', {}).get('model', '')}")
    lines.append(f"tokens_per_second,{data.get('tokens_per_second', '')}")
    lines.append(f"ttft_ms,{data.get('ttft_ms', '')}")
    lines.append(f"requests_per_second,{data.get('requests_per_second', '')}")
    lines.append(f"total_tokens,{data.get('total_tokens', '')}")
    lines.append(f"total_requests,{data.get('total_requests', '')}")
    lines.append(f"duration_seconds,{data.get('duration_seconds', '')}")
    lines.append(f"cpu_utilization_percent,{data.get('cpu_utilization_percent', '')}")
    lines.append(f"memory_mb,{data.get('memory_mb', '')}")
    lat = data.get("latency", {})
    for k in ["p50_ms", "p75_ms", "p90_ms", "p95_ms", "p99_ms", "avg_ms", "min_ms", "max_ms"]:
        lines.append(f"latency_{k},{lat.get(k, '')}")
    return "\n".join(lines)


def _benchmark_to_html(data: dict) -> str:
    """Convert benchmark data to a simple HTML report."""
    cfg = data.get("config", {})
    lat = data.get("latency", {})
    return f"""<!DOCTYPE html>
<html><head><title>ArmPilot Benchmark {data.get('id', '')}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#f5f5f5}}</style></head>
<body>
<h1>ArmPilot-AI Benchmark Report</h1>
<p><strong>ID:</strong> {data.get('id', '')}</p>
<p><strong>Status:</strong> {data.get('status', '')}</p>
<p><strong>Model:</strong> {cfg.get('model', '')}</p>
<h2>Results</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Tokens/sec</td><td>{data.get('tokens_per_second', 'N/A')}</td></tr>
<tr><td>TTFT</td><td>{data.get('ttft_ms', 'N/A')} ms</td></tr>
<tr><td>Requests/sec</td><td>{data.get('requests_per_second', 'N/A')}</td></tr>
<tr><td>Total Tokens</td><td>{data.get('total_tokens', 0)}</td></tr>
<tr><td>Duration</td><td>{data.get('duration_seconds', 'N/A')} s</td></tr>
</table>
<h2>Latency</h2>
<table>
<tr><th>Percentile</th><th>Value</th></tr>
<tr><td>P50</td><td>{lat.get('p50_ms', 'N/A')} ms</td></tr>
<tr><td>P90</td><td>{lat.get('p90_ms', 'N/A')} ms</td></tr>
<tr><td>P95</td><td>{lat.get('p95_ms', 'N/A')} ms</td></tr>
<tr><td>P99</td><td>{lat.get('p99_ms', 'N/A')} ms</td></tr>
</table>
</body></html>"""


def _optimization_to_csv(data: dict) -> str:
    """Convert optimization data to CSV."""
    lines = ["metric,value"]
    lines.append(f"id,{data.get('id', '')}")
    lines.append(f"model,{data.get('config', {}).get('model', '')}")
    lines.append(f"objective,{data.get('config', {}).get('objective', '')}")
    best = data.get("best_candidate")
    if best:
        lines.append(f"best_name,{best.get('name', '')}")
        lines.append(f"best_tps,{best.get('tokens_per_second', '')}")
        lines.append(f"best_ttft,{best.get('ttft_ms', '')}")
    return "\n".join(lines)


def _optimization_to_html(data: dict) -> str:
    """Convert optimization data to HTML."""
    cfg = data.get("config", {})
    best = data.get("best_candidate")
    candidates = data.get("candidates", [])

    rows = ""
    for c in candidates:
        rows += f"""<tr>
<td>{c.get('name', '')}</td>
<td>{c.get('tokens_per_second', 'N/A')}</td>
<td>{c.get('ttft_ms', 'N/A')}</td>
<td>{c.get('memory_mb', 'N/A')}</td>
<td>{c.get('status', '')}</td>
</tr>"""

    return f"""<!DOCTYPE html>
<html><head><title>ArmPilot Optimization {data.get('id', '')}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#f5f5f5}}</style></head>
<body>
<h1>ArmPilot-AI Optimization Report</h1>
<p><strong>Model:</strong> {cfg.get('model', '')}</p>
<p><strong>Objective:</strong> {cfg.get('objective', '')}</p>
{"<h2>Best Configuration</h2><p><strong>" + best.get('name', '') + "</strong></p><p>Tokens/sec: " + str(best.get('tokens_per_second', 'N/A')) + "</p>" if best else ""}
<h2>All Candidates</h2>
<table>
<tr><th>Name</th><th>TPS</th><th>TTFT</th><th>Memory</th><th>Status</th></tr>
{rows}
</table>
</body></html>"""
