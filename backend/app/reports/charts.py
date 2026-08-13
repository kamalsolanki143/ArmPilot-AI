"""
ArmPilot-AI — Chart Generation
Generates SVG chart strings for embedding in HTML reports.
Uses plain Python — no external charting library required.
"""

from __future__ import annotations

import html
import math
from typing import Any, Optional

from app.schemas.benchmark import BenchmarkResult, LatencyMetrics
from app.schemas.optimization import OptimizationCandidate


def render_latency_chart(latency: LatencyMetrics) -> Optional[str]:
    """Render an SVG bar chart of latency percentiles."""
    labels = ["P50", "P75", "P90", "P95", "P99"]
    values = [latency.p50_ms, latency.p75_ms, latency.p90_ms, latency.p95_ms, latency.p99_ms]

    if all(v == 0 for v in values):
        return None

    colors_list = ["#22c55e", "#22c55e", "#eab308", "#f97316", "#ef4444"]
    return _bar_svg(labels, values, colors_list, "ms")


def render_throughput_chart(result: BenchmarkResult) -> Optional[str]:
    """Render an SVG bar chart for throughput metrics."""
    labels = ["Tokens/sec", "Requests/sec"]
    values = [
        result.tokens_per_second or 0,
        (result.requests_per_second or 0) * 100,  # Scale for visibility
    ]

    if all(v == 0 for v in values):
        return None

    colors_list = ["#6366f1", "#8b5cf6"]
    chart = _bar_svg(labels, values, colors_list)
    # Add secondary labels for requests/sec
    if result.requests_per_second:
        chart = chart.replace(
            f"<text x=",
            f"<text x=",
        )
    return chart


def render_resource_usage_chart(
    cpu: Optional[float] = None,
    memory: Optional[float] = None,
    model_size: Optional[float] = None,
) -> Optional[str]:
    """Render an SVG bar chart for resource usage."""
    labels = []
    values = []
    colors_list = []

    if cpu is not None:
        labels.append("CPU %")
        values.append(cpu)
        colors_list.append("#f97316")
    if memory is not None:
        labels.append("Memory MB")
        values.append(memory)
        colors_list.append("#6366f1")
    if model_size is not None:
        labels.append("Model MB")
        values.append(model_size)
        colors_list.append("#8b5cf6")

    if not values or all(v == 0 for v in values):
        return None

    return _bar_svg(labels, values, colors_list)


def render_optimization_comparison_chart(
    candidates: list[OptimizationCandidate],
) -> Optional[str]:
    """Render an SVG grouped bar chart comparing optimization candidates."""
    completed = [c for c in candidates if c.status == "completed" and c.tokens_per_second is not None]
    if not completed:
        return None

    # Take top 8 by throughput
    completed.sort(key=lambda c: c.tokens_per_second or 0, reverse=True)
    top = completed[:8]

    labels = [c.name[:12] for c in top]
    values = [c.tokens_per_second or 0 for c in top]
    colors_list = _gradient("#6366f1", "#22c55e", len(top))

    return _bar_svg(labels, values, colors_list, "tok/s")


def render_latency_percentile_line(latency: LatencyMetrics) -> Optional[str]:
    """Render an SVG line chart of latency percentiles."""
    labels = ["P50", "P75", "P90", "P95", "P99"]
    values = [latency.p50_ms, latency.p75_ms, latency.p90_ms, latency.p95_ms, latency.p99_ms]

    if all(v == 0 for v in values):
        return None

    return _line_svg(labels, values, "#6366f1", "ms")


# ── SVG Helpers ──────────────────────────────────────────────────────────

def _bar_svg(
    labels: list[str],
    values: list[float],
    fill_colors: list[str],
    unit: str = "",
) -> str:
    """Generate a horizontal bar chart SVG."""
    n = len(labels)
    if n == 0:
        return ""

    W, H = 480, max(180, n * 36 + 60)
    pad_top, pad_right, pad_bottom, pad_left = 30, 20, 30, 90
    pw = W - pad_left - pad_right
    ph = H - pad_top - pad_bottom
    max_val = max(values) * 1.15 or 1
    bar_h = min(28, (ph / n) * 0.7)
    spacing = ph / n

    bars: list[str] = []
    for i, (label, val, color) in enumerate(zip(labels, values, fill_colors)):
        y = pad_top + i * spacing + (spacing - bar_h) / 2
        bar_w = (val / max_val) * pw
        bars.append(
            f'<rect x="{pad_left}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" '
            f'rx="4" fill="{color}" opacity="0.85"/>'
        )
        # Value label
        val_text = f"{val:.1f} {unit}".strip() if isinstance(val, float) and val != int(val) else f"{int(val)} {unit}".strip()
        bars.append(
            f'<text x="{pad_left + bar_w + 6}" y="{y + bar_h / 2 + 4}" '
            f'font-size="11" fill="#a1a1aa" font-family="sans-serif">{html.escape(val_text)}</text>'
        )
        # Label
        bars.append(
            f'<text x="{pad_left - 8}" y="{y + bar_h / 2 + 4}" '
            f'font-size="11" fill="#a1a1aa" text-anchor="end" '
            f'font-family="sans-serif">{html.escape(label)}</text>'
        )

    # Grid lines
    grid: list[str] = []
    for i in range(5):
        x = pad_left + (pw / 4) * i
        val = (max_val / 4) * i
        grid.append(
            f'<line x1="{x}" y1="{pad_top}" x2="{x}" y2="{pad_top + ph}" '
            f'stroke="#e5e7eb" stroke-width="0.5" stroke-dasharray="3,3"/>'
        )
        grid.append(
            f'<text x="{x}" y="{H - pad_bottom + 16}" font-size="10" fill="#a1a1aa" '
            f'text-anchor="middle" font-family="sans-serif">{val:.0f}</text>'
        )

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{W}px;height:auto;background:#0f1117;border-radius:8px">'
        f'{"".join(grid)}{"".join(bars)}</svg>'
    )


def _line_svg(
    labels: list[str],
    values: list[float],
    stroke_color: str,
    unit: str = "",
) -> str:
    """Generate a line chart SVG."""
    n = len(labels)
    if n == 0:
        return ""

    W, H = 480, 200
    pad_top, pad_right, pad_bottom, pad_left = 30, 30, 40, 60
    pw = W - pad_left - pad_right
    ph = H - pad_top - pad_bottom
    max_val = max(values) * 1.15 or 1

    points: list[str] = []
    for i, val in enumerate(values):
        x = pad_left + (i / (n - 1)) * pw if n > 1 else pad_left + pw / 2
        y = pad_top + ph - (val / max_val) * ph
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    dots = []
    labels_svg = []
    for i, (label, val) in enumerate(zip(labels, values)):
        x = pad_left + (i / (n - 1)) * pw if n > 1 else pad_left + pw / 2
        y = pad_top + ph - (val / max_val) * ph
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{stroke_color}" stroke="#0f1117" stroke-width="2"/>'
        )
        val_text = f"{val:.1f} {unit}".strip()
        labels_svg.append(
            f'<text x="{x:.1f}" y="{y - 10}" font-size="10" fill="#a1a1aa" '
            f'text-anchor="middle" font-family="sans-serif">{html.escape(val_text)}</text>'
        )
        labels_svg.append(
            f'<text x="{x:.1f}" y="{H - pad_bottom + 16}" font-size="10" fill="#a1a1aa" '
            f'text-anchor="middle" font-family="sans-serif">{html.escape(label)}</text>'
        )

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{W}px;height:auto;background:#0f1117;border-radius:8px">'
        f'<polyline points="{polyline}" fill="none" stroke="{stroke_color}" stroke-width="2.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'{"".join(dots)}{"".join(labels_svg)}</svg>'
    )


def _gradient(start: str, end: str, n: int) -> list[str]:
    """Generate n colors between two hex colors."""
    if n <= 1:
        return [start]

    def _hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _rgb_to_hex(r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    sr, sg, sb = _hex_to_rgb(start)
    er, eg, eb = _hex_to_rgb(end)

    result: list[str] = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        r = int(sr + (er - sr) * t)
        g = int(sg + (eg - sg) * t)
        b = int(sb + (eb - sb) * t)
        result.append(_rgb_to_hex(r, g, b))

    return result
