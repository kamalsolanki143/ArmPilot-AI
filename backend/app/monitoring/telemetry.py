"""
ArmPilot-AI — OpenTelemetry Integration
Configures OTLP tracing and metrics export. Falls back gracefully when
opentelemetry packages are not installed.
"""

from __future__ import annotations

import os
from typing import Optional

from app.core.config import settings
from app.core.logger import logger

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
        ConsoleMetricExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

from app.monitoring.metrics import update_system_metrics, update_model_state


class TelemetryManager:
    """Manages OpenTelemetry providers, tracers, and meters."""

    def __init__(self) -> None:
        self._initialized = False
        self._tracer: Optional[object] = None
        self._meter: Optional[object] = None
        self._trace_provider: Optional[object] = None
        self._meter_provider: Optional[object] = None

    @property
    def enabled(self) -> bool:
        return HAS_OTEL and self._initialized

    def initialize(
        self,
        service_name: str = "armpilot-ai",
        otlp_endpoint: Optional[str] = None,
        enable_console_export: bool = False,
    ) -> None:
        """Set up OTLP exporters and register global providers."""
        if not HAS_OTEL:
            logger.info("OpenTelemetry packages not installed; telemetry disabled")
            return

        endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        resource = Resource.create({SERVICE_NAME: service_name})

        # ── Tracing ──────────────────────────────────────────────────
        trace_provider = TracerProvider(resource=resource)

        if endpoint:
            try:
                span_exporter = OTLPSpanExporter(endpoint=endpoint)
                trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
                logger.info("OTLP trace exporter configured → %s", endpoint)
            except Exception as exc:
                logger.warning("Failed to configure OTLP trace exporter: %s", exc)

        if enable_console_export or not endpoint:
            trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(trace_provider)
        self._trace_provider = trace_provider
        self._tracer = trace.get_tracer(service_name)

        # ── Metrics ──────────────────────────────────────────────────
        metric_readers = []
        if endpoint:
            try:
                metric_exporter = OTLPMetricExporter(endpoint=endpoint)
                metric_readers.append(
                    PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30000)
                )
                logger.info("OTLP metric exporter configured → %s", endpoint)
            except Exception as exc:
                logger.warning("Failed to configure OTLP metric exporter: %s", exc)

        if enable_console_export or not endpoint:
            metric_readers.append(
                PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=30000)
            )

        if metric_readers:
            meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
            metrics.set_meter_provider(meter_provider)
            self._meter_provider = meter_provider
            self._meter = metrics.get_meter(service_name)

        self._initialized = True
        logger.info("OpenTelemetry telemetry initialized (service=%s)", service_name)

    def get_tracer(self) -> Optional[object]:
        """Return the configured tracer, or None if unavailable."""
        return self._tracer

    def get_meter(self) -> Optional[object]:
        """Return the configured meter, or None if unavailable."""
        return self._meter

    def shutdown(self) -> None:
        """Flush and shut down all exporters."""
        if not self._initialized:
            return
        try:
            if self._trace_provider is not None and hasattr(self._trace_provider, "shutdown"):
                self._trace_provider.shutdown()
            if self._meter_provider is not None and hasattr(self._meter_provider, "shutdown"):
                self._meter_provider.shutdown()
        except Exception as exc:
            logger.warning("Error shutting down telemetry: %s", exc)
        self._initialized = False
        logger.info("OpenTelemetry telemetry shut down")

    def create_counter(self, name: str, description: str = "") -> Optional[object]:
        """Create an OTLP counter instrument."""
        if not self.enabled or self._meter is None:
            return None
        try:
            return self._meter.create_counter(name, description=description)  # type: ignore[union-attr]
        except Exception:
            return None

    def create_histogram(self, name: str, description: str = "") -> Optional[object]:
        """Create an OTLP histogram instrument."""
        if not self.enabled or self._meter is None:
            return None
        try:
            return self._meter.create_histogram(name, description=description)  # type: ignore[union-attr]
        except Exception:
            return None

    def create_gauge(self, name: str, description: str = "") -> Optional[object]:
        """Create an OTLP gauge instrument."""
        if not self.enabled or self._meter is None:
            return None
        try:
            return self._meter.create_observable_gauge(  # type: ignore[union-attr]
                name,
                callbacks=[lambda: [metrics.Observation(0, {})]],
                description=description,
            )
        except Exception:
            return None


# Singleton
telemetry_manager = TelemetryManager()
