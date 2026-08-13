"""
ArmPilot-AI — Inference Runtime Abstraction
Abstract base class + LlamaCpp implementation.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generator, Optional

from app.core.logger import logger


class InferenceRuntime(ABC):
    """Abstract base class for inference runtimes."""

    name: str = "base"

    @abstractmethod
    def load_model(self, model_path: str, **kwargs: Any) -> None:
        """Load a model from the given path."""
        ...

    @abstractmethod
    def unload_model(self) -> None:
        """Unload the currently loaded model and free resources."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Generate a complete response.
        Returns dict with keys: text, tokens, ttft_ms, generation_time_ms, tokens_per_second
        """
        ...

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Stream tokens one at a time.
        Yields dicts with keys: token, is_first, is_last, ttft_ms (on first)
        """
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        ...

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Return metadata about the loaded model."""
        ...


class LlamaCppRuntime(InferenceRuntime):
    """Inference runtime using llama-cpp-python."""

    name = "llama.cpp"

    def __init__(self) -> None:
        self._model: Any = None
        self._model_path: str = ""
        self._model_info: dict[str, Any] = {}
        self._load_kwargs: dict[str, Any] = {}

    def load_model(self, model_path: str, **kwargs: Any) -> None:
        """Load a GGUF model using llama-cpp-python."""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise RuntimeError(
                "llama-cpp-python is not installed. "
                "Install with: pip install llama-cpp-python"
            )

        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        logger.info("Loading model: %s", model_path)
        load_start = time.perf_counter()

        n_ctx = kwargs.get("n_ctx", 2048)
        n_threads = kwargs.get("n_threads", 4)
        n_batch = kwargs.get("n_batch", 512)
        n_gpu_layers = kwargs.get("n_gpu_layers", 0)
        verbose = kwargs.get("verbose", False)

        self._model = Llama(
            model_path=str(path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=n_batch,
            n_gpu_layers=n_gpu_layers,
            verbose=verbose,
        )

        load_time = (time.perf_counter() - load_start) * 1000
        self._model_path = model_path

        # Extract model metadata
        file_size_mb = path.stat().st_size / (1024 ** 2)
        self._model_info = {
            "path": model_path,
            "file_name": path.name,
            "file_size_mb": round(file_size_mb, 1),
            "n_ctx": n_ctx,
            "n_threads": n_threads,
            "n_batch": n_batch,
            "n_gpu_layers": n_gpu_layers,
            "load_time_ms": round(load_time, 1),
        }
        self._load_kwargs = kwargs

        logger.info("Model loaded in %.1fms (%.1f MB)", load_time, file_size_mb)

    def unload_model(self) -> None:
        """Unload the current model."""
        if self._model is not None:
            del self._model
            self._model = None
            self._model_path = ""
            self._model_info = {}
            logger.info("Model unloaded")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a complete response."""
        if not self.is_loaded():
            raise RuntimeError("No model loaded")

        gen_start = time.perf_counter()

        result = self._model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
            echo=False,
        )

        gen_time_ms = (time.perf_counter() - gen_start) * 1000
        text = result["choices"][0]["text"]
        prompt_tokens = result["usage"]["prompt_tokens"]
        completion_tokens = result["usage"]["completion_tokens"]
        total_tokens = result["usage"]["total_tokens"]

        tokens_per_second = (completion_tokens / (gen_time_ms / 1000)) if gen_time_ms > 0 else 0

        return {
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "generation_time_ms": round(gen_time_ms, 2),
            "tokens_per_second": round(tokens_per_second, 2),
        }

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Stream tokens one at a time."""
        if not self.is_loaded():
            raise RuntimeError("No model loaded")

        stream_start = time.perf_counter()
        first_token_time: float | None = None
        token_count = 0

        stream = self._model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
            echo=False,
            stream=True,
        )

        for chunk in stream:
            token_count += 1
            now = time.perf_counter()
            text = chunk["choices"][0]["text"]

            is_first = first_token_time is None
            if is_first:
                first_token_time = now

            is_last = chunk["choices"][0].get("finish_reason") is not None

            result: dict[str, Any] = {
                "token": text,
                "is_first": is_first,
                "is_last": is_last,
            }

            if is_first:
                result["ttft_ms"] = round((now - stream_start) * 1000, 2)

            if is_last:
                total_time = (now - stream_start) * 1000
                result["total_tokens"] = token_count
                result["generation_time_ms"] = round(total_time, 2)
                result["tokens_per_second"] = round(
                    token_count / (total_time / 1000) if total_time > 0 else 0, 2
                )

            yield result

    def is_loaded(self) -> bool:
        return self._model is not None

    def get_model_info(self) -> dict[str, Any]:
        return self._model_info.copy()


# ── Runtime Registry ──────────────────────────────────────────────────────────

_RUNTIMES: dict[str, type[InferenceRuntime]] = {
    "llama.cpp": LlamaCppRuntime,
}


def get_runtime(name: str) -> InferenceRuntime:
    """Get an inference runtime instance by name."""
    cls = _RUNTIMES.get(name)
    if cls is None:
        available = ", ".join(_RUNTIMES.keys())
        raise ValueError(f"Unknown runtime '{name}'. Available: {available}")
    return cls()


def list_runtimes() -> list[str]:
    """List available runtime names."""
    return list(_RUNTIMES.keys())
