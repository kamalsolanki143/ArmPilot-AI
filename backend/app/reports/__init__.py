"""
ArmPilot-AI — Reports Package
Provides benchmark and optimization report generation in multiple formats.
"""

from app.reports.report_builder import (
    generate_benchmark_report,
    generate_optimization_report,
)
from app.reports.html import (
    generate_benchmark_html,
    generate_optimization_html,
)
from app.reports.csv import (
    generate_benchmark_csv,
    generate_optimization_csv,
    generate_candidates_csv,
    generate_latency_csv,
)
from app.reports.exporter import ReportExporter, report_exporter
from app.reports.charts import (
    render_latency_chart,
    render_throughput_chart,
    render_resource_usage_chart,
    render_optimization_comparison_chart,
    render_latency_percentile_line,
)

__all__ = [
    # Markdown
    "generate_benchmark_report",
    "generate_optimization_report",
    # HTML
    "generate_benchmark_html",
    "generate_optimization_html",
    # CSV
    "generate_benchmark_csv",
    "generate_optimization_csv",
    "generate_candidates_csv",
    "generate_latency_csv",
    # PDF (lazy — requires reportlab)
    # Exporter
    "ReportExporter",
    "report_exporter",
    # Charts
    "render_latency_chart",
    "render_throughput_chart",
    "render_resource_usage_chart",
    "render_optimization_comparison_chart",
    "render_latency_percentile_line",
]
