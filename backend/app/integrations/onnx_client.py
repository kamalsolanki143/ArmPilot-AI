"""
ArmPilot-AI — ONNX Runtime Client
Client for running inference via ONNX Runtime with ARM optimizations.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Generator, Optional

from app.core.logger import logger


class OnnxClient:
    """Client for ONNX Runtime inference execution."""

    def __init__(self) -> None:
        self._session: Any = None
        self._model_path: str = ""
        self._input_names: list[str] = []
        self._output_names: list[str] = []

    @property
    def is_loaded(self) -> bool:
        return self._session is not None

    def load_model(
        self,
        model_path: str,
        providers: Optional[list[str]] = None,
        session_options: Optional[dict[str, Any]] = None,
    ) -> None:
        """Load an ONNX model for inference."""
        try:
            import onnxruntime as ort
        except ImportError:
            raise RuntimeError(
                "onnxruntime is not installed. "
                "Install with: pip install onnxruntime"
            )

        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")

        # Default to CPU execution provider with ARM optimizations
        if providers is None:
            providers = ["CPUExecutionProvider"]

        opts = ort.SessionOptions()
        if session_options:
            for key, val in session_options.items():
                if hasattr(opts, key):
                    setattr(opts, key, val)

        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        logger.info("Loading ONNX model: %s (providers=%s)", model_path, providers)
        start = time.perf_counter()

        self._session = ort.InferenceSession(
            str(path),
            sess_options=opts,
            providers=providers,
        )

        self._input_names = [inp.name for inp in self._session.get_inputs()]
        self._output_names = [out.name for out in self._session.get_outputs()]
        self._model_path = model_path

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("ONNX model loaded in %.1fms", elapsed)

    def unload_model(self) -> None:
        """Unload the current model."""
        self._session = None
        self._model_path = ""
        self._input_names = []
        self._output_names = []
        logger.info("ONNX model unloaded")

    def run_inference(
        self,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a single inference pass."""
        if self._session is None:
            raise RuntimeError("No ONNX model loaded")

        start = time.perf_counter()
        outputs = self._session.run(self._output_names, input_data)
        elapsed_ms = (time.perf_counter() - start) * 1000

        result: dict[str, Any] = {
            "latency_ms": round(elapsed_ms, 2),
            "outputs": {},
        }

        for name, value in zip(self._output_names, outputs):
            result["outputs"][name] = value.tolist() if hasattr(value, "tolist") else value

        return result

    def benchmark(
        self,
        input_data: dict[str, Any],
        num_runs: int = 10,
    ) -> dict[str, Any]:
        """Benchmark the loaded ONNX model."""
        if self._session is None:
            raise RuntimeError("No ONNX model loaded")

        latencies: list[float] = []

        # Warmup
        for _ in range(min(3, num_runs)):
            self._session.run(self._output_names, input_data)

        # Benchmark
        for _ in range(num_runs):
            start = time.perf_counter()
            self._session.run(self._output_names, input_data)
            latencies.append((time.perf_counter() - start) * 1000)

        latencies.sort()
        avg = sum(latencies) / len(latencies)

        return {
            "num_runs": num_runs,
            "avg_latency_ms": round(avg, 2),
            "min_latency_ms": round(latencies[0], 2),
            "max_latency_ms": round(latencies[-1], 2),
            "p50_latency_ms": round(latencies[len(latencies) // 2], 2),
            "p95_latency_ms": round(latencies[int(len(latencies) * 0.95)], 2),
            "throughput_per_sec": round(1000 / avg, 2) if avg > 0 else 0,
        }

    def get_info(self) -> dict[str, Any]:
        """Get information about the loaded model."""
        if self._session is None:
            return {"loaded": False}

        providers = self._session.get_providers()
        return {
            "loaded": True,
            "model_path": self._model_path,
            "input_names": self._input_names,
            "output_names": self._output_names,
            "providers": providers,
        }


# Singleton
onnx_client = OnnxClient()
