"""
ArmPilot-AI — HTML Report Generator
Renders benchmark/optimization reports as self-contained HTML documents.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from html import escape

from app.schemas.benchmark import BenchmarkResult, LatencyMetrics
from app.schemas.optimization import OptimizationResult, OptimizationCandidate
from app.reports.charts import (
    render_latency_chart,
    render_optimization_comparison_chart,
    render_resource_usage_chart,
    render_throughput_chart,
)


def generate_benchmark_html(
    result: BenchmarkResult,
    *,
    include_charts: bool = True,
    include_hardware: bool = True,
    include_reproduction: bool = True,
) -> str:
    """Generate a self-contained HTML report for a benchmark run."""
    hw = result.hardware or {}
    cfg = result.config
    ts = result.timestamp or datetime.now(timezone.utc).isoformat()

    sections: list[str] = []

    # Header
    sections.append(_header(f"Benchmark Report — {escape(cfg.model)}", ts))

    # Status badge
    sections.append(_status_badge(result.status))

    # Metadata
    sections.append(_kv_table({
        "Report ID": result.id,
        "Timestamp": ts,
        "Model": cfg.model,
        "Runtime": cfg.runtime,
        "Quantization": cfg.quantization or "Default",
    }))

    # Hardware section
    if include_hardware and hw:
        sections.append(_section("Hardware", _kv_table({
            "Architecture": hw.get("architecture", "N/A"),
            "CPU Model": hw.get("cpu_model", "N/A"),
            "CPU Cores": f"{hw.get('cpu_count', 'N/A')} (physical: {hw.get('cpu_count_physical', 'N/A')})",
            "Memory": f"{hw.get('memory_total_gb', 'N/A')} GB",
            "ARM64": "Yes" if hw.get("is_arm64") else "No",
            "Platform": hw.get("platform", "N/A"),
        })))

    # Configuration
    sections.append(_section("Configuration", _kv_table({
        "Batch Size": cfg.batch_size,
        "Threads": cfg.threads,
        "Concurrency": cfg.concurrency,
        "Num Requests": cfg.num_requests,
        "Max Tokens": cfg.max_tokens,
        "Warmup Requests": cfg.warmup_requests,
    })))

    # Results
    sections.append(_section("Results", _kv_table({
        "TTFT": _fmt(result.ttft_ms, "ms"),
        "Tokens/sec": _fmt(result.tokens_per_second),
        "Requests/sec": _fmt(result.requests_per_second),
        "Total Tokens": result.total_tokens,
        "Total Requests": result.total_requests,
        "Duration": _fmt(result.duration_seconds, "s"),
    })))

    # Latency
    lat = result.latency
    sections.append(_section("Latency Distribution", _kv_table({
        "P50": _fmt(lat.p50_ms, "ms"),
        "P75": _fmt(lat.p75_ms, "ms"),
        "P90": _fmt(lat.p90_ms, "ms"),
        "P95": _fmt(lat.p95_ms, "ms"),
        "P99": _fmt(lat.p99_ms, "ms"),
        "Avg": _fmt(lat.avg_ms, "ms"),
        "Min": _fmt(lat.min_ms, "ms"),
        "Max": _fmt(lat.max_ms, "ms"),
    })))

    # Resource usage
    sections.append(_section("Resource Usage", _kv_table({
        "CPU Utilization": _fmt(result.cpu_utilization_percent, "%"),
        "Memory (RSS)": _fmt(result.memory_mb, "MB"),
        "Memory Peak": _fmt(result.memory_peak_mb, "MB"),
        "Model Size": _fmt(result.model_size_mb, "MB"),
    })))

    # Charts
    if include_charts:
        chart_sections: list[str] = []
        latency_chart = render_latency_chart(result.latency)
        if latency_chart:
            chart_sections.append(_chart_card("Latency Distribution", latency_chart))
        throughput_chart = render_throughput_chart(result)
        if throughput_chart:
            chart_sections.append(_chart_card("Throughput", throughput_chart))
        resource_chart = render_resource_usage_chart(
            cpu=result.cpu_utilization_percent,
            memory=result.memory_mb,
            model_size=result.model_size_mb,
        )
        if resource_chart:
            chart_sections.append(_chart_card("Resource Usage", resource_chart))
        if chart_sections:
            sections.append(_section("Charts", '<div class="charts-grid">' + "".join(chart_sections) + "</div>"))

    # Reproduction command
    if include_reproduction:
        cmd = (
            f"arm-infer benchmark \\\n"
            f"  --model {escape(cfg.model)} \\\n"
            f"  --runtime {escape(cfg.runtime)} \\\n"
            f"  --batch-size {cfg.batch_size} \\\n"
            f"  --threads {cfg.threads} \\\n"
            f"  --concurrency {cfg.concurrency} \\\n"
            f"  --num-requests {cfg.num_requests} \\\n"
            f"  --max-tokens {cfg.max_tokens}"
        )
        sections.append(_section("Reproduction", f'<pre class="code-block"><code>{escape(cmd)}</code></pre>'))

    # Footer
    sections.append(_footer(ts))

    return _page("Benchmark Report", "".join(sections))


def generate_optimization_html(
    result: OptimizationResult,
    *,
    include_charts: bool = True,
    include_hardware: bool = True,
    include_reproduction: bool = True,
) -> str:
    """Generate a self-contained HTML report for an optimization run."""
    ts = result.timestamp or datetime.now(timezone.utc).isoformat()

    sections: list[str] = []
    sections.append(_header(f"Optimization Report — {escape(result.config.model)}", ts))
    sections.append(_status_badge(result.status))

    sections.append(_kv_table({
        "Report ID": result.id,
        "Timestamp": ts,
        "Model": result.config.model,
        "Objective": result.config.objective,
        "Status": result.status,
    }))

    # Baseline
    if result.baseline:
        baseline_rows = {k: v for k, v in result.baseline.items() if k != "benchmark_id"}
        sections.append(_section("Baseline", _kv_table(baseline_rows)))

    # Best candidate
    if result.best_candidate:
        bc = result.best_candidate
        sections.append(_section("Best Configuration", _candidate_detail(bc)))

    # Improvement summary
    if result.improvement_summary:
        rows = []
        for metric, data in result.improvement_summary.items():
            if isinstance(data, dict):
                rows.append({
                    "Metric": metric,
                    "Before": data.get("before", "N/A"),
                    "After": data.get("after", "N/A"),
                    "Change": f"{data.get('change_percent', 0):+.1f}%",
                })
        if rows:
            sections.append(_section("Improvements", _data_table(
                ["Metric", "Before", "After", "Change"], rows
            )))

    # All candidates
    if result.candidates:
        rows = []
        for c in result.candidates:
            rows.append({
                "Name": c.name,
                "Tokens/sec": _fmt(c.tokens_per_second),
                "TTFT": _fmt(c.ttft_ms, "ms"),
                "P95 Latency": _fmt(c.p95_latency_ms, "ms"),
                "Memory": _fmt(c.memory_mb, "MB"),
                "Status": c.status,
            })
        sections.append(_section("All Candidates", _data_table(
            ["Name", "Tokens/sec", "TTFT", "P95 Latency", "Memory", "Status"], rows
        )))

    # Charts
    if include_charts and result.candidates:
        chart = render_optimization_comparison_chart(result.candidates)
        if chart:
            sections.append(_section("Charts", f'<div class="charts-grid">{_chart_card("Comparison", chart)}</div>'))

    sections.append(_footer(ts))
    return _page("Optimization Report", "".join(sections))


# ── HTML helpers ──────────────────────────────────────────────────────────

_CSS = """
:root {
  --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
  --text: #e4e4e7; --muted: #a1a1aa; --accent: #6366f1;
  --green: #22c55e; --red: #ef4444; --yellow: #eab308;
  --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem; }
.container { max-width: 960px; margin: 0 auto; }
h1 { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
h2 { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--accent); }
.subtitle { color: var(--muted); font-size: 0.875rem; margin-bottom: 2rem; }
.section { background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1.5rem; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border); font-size: 0.875rem; }
th { color: var(--muted); font-weight: 500; }
.badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
.badge-completed { background: rgba(34,197,94,0.15); color: var(--green); }
.badge-running { background: rgba(234,179,8,0.15); color: var(--yellow); }
.badge-failed { background: rgba(239,68,68,0.15); color: var(--red); }
.badge-pending { background: rgba(161,161,170,0.15); color: var(--muted); }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1rem; }
.chart-card { background: var(--bg); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; text-align: center; }
.chart-card h3 { font-size: 0.875rem; color: var(--muted); margin-bottom: 0.5rem; }
.code-block { background: var(--bg); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; overflow-x: auto; font-family: var(--mono); font-size: 0.8rem; color: var(--muted); }
footer { text-align: center; color: var(--muted); font-size: 0.75rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); }
"""

_JS_CHART_TEMPLATE = """
<script>
(function() {{
  var canvas = document.getElementById('{chart_id}');
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');
  var data = {chart_data};
  var W = canvas.width, H = canvas.height;
  var pad = {{ top: 30, right: 20, bottom: 40, left: 60 }};
  var pw = W - pad.left - pad.right, ph = H - pad.top - pad.bottom;
  var max = Math.max.apply(null, data.values) * 1.15 || 1;
  var barW = (pw / data.values.length) * 0.6;
  var gap = (pw / data.values.length) * 0.4;
  ctx.fillStyle = '#e4e4e7';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'center';
  data.values.forEach(function(v, i) {{
    var x = pad.left + i * (barW + gap) + gap / 2;
    var h = (v / max) * ph;
    var y = pad.top + ph - h;
    ctx.fillStyle = data.colors ? data.colors[i] : '#6366f1';
    ctx.fillRect(x, y, barW, h);
    ctx.fillStyle = '#a1a1aa';
    ctx.fillText(v.toFixed(1), x + barW / 2, y - 6);
    ctx.fillText(data.labels[i], x + barW / 2, H - pad.bottom + 16);
  }});
  ctx.fillStyle = '#a1a1aa';
  ctx.textAlign = 'right';
  for (var i = 0; i <= 4; i++) {{
    var v = (max / 4) * i;
    var y = pad.top + ph - (v / max) * ph;
    ctx.fillText(v.toFixed(1), pad.left - 8, y + 4);
    ctx.strokeStyle = '#2a2d3a';
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + pw, y); ctx.stroke();
  }}
}})();
</script>
"""


def _page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        f"<meta charset=\"utf-8\">\n"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{escape(title)} — ArmPilot-AI</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f'<div class="container">{body}</div>\n'
        "</body>\n"
        "</html>"
    )


def _header(title: str, ts: str) -> str:
    return (
        f"<h1>{escape(title)}</h1>\n"
        f'<p class="subtitle">Generated by ArmPilot-AI — {escape(ts)}</p>'
    )


def _footer(ts: str) -> str:
    return f"<footer>ArmPilot-AI &mdash; Generated at {escape(ts)}</footer>"


def _status_badge(status: str) -> str:
    cls = f"badge-{status}" if status in ("completed", "running", "failed", "pending") else ""
    return f'<p style="margin-bottom:1.5rem"><span class="badge {cls}">{escape(status)}</span></p>'


def _section(title: str, content: str) -> str:
    return f'<div class="section"><h2>{escape(title)}</h2>{content}</div>'


def _kv_table(data: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><th>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>"
        for k, v in data.items()
    )
    return f"<table>{rows}</table>"


def _data_table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    ths = "".join(f"<th>{escape(h)}</th>" for h in headers)
    trs = []
    for row in rows:
        tds = "".join(f"<td>{escape(str(row.get(h, '')))}</td>" for h in headers)
        trs.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{ths}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def _candidate_detail(c: OptimizationCandidate) -> str:
    return _kv_table({
        "Name": c.name,
        "Description": c.description,
        "Tokens/sec": _fmt(c.tokens_per_second),
        "TTFT": _fmt(c.ttft_ms, "ms"),
        "P95 Latency": _fmt(c.p95_latency_ms, "ms"),
        "Memory": _fmt(c.memory_mb, "MB"),
        "Status": c.status,
    })


def _chart_card(title: str, chart_html: str) -> str:
    return f'<div class="chart-card"><h3>{escape(title)}</h3>{chart_html}</div>'


def _fmt(value: Any, unit: str = "") -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.1f} {unit}".strip()
    return f"{value} {unit}".strip()
