"""
ArmPilot-AI — OpenAI API Client
Client for benchmarking against OpenAI API models as reference baselines.
"""

from __future__ import annotations

import os
import time
from typing import Any, Generator, Optional

from app.core.logger import logger


class OpenAIClient:
    """Client for interacting with OpenAI-compatible APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url or "https://api.openai.com/v1"
        self._timeout = timeout
        self._client: Any = None

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> Any:
        """Lazy-init the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise RuntimeError(
                    "openai package is not installed. "
                    "Install with: pip install openai"
                )
            kwargs: dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def list_models(self) -> list[dict[str, Any]]:
        """List available models from the API."""
        client = self._get_client()
        models = client.models.list()
        return [
            {"id": m.id, "owned_by": getattr(m, "owned_by", "")}
            for m in models.data
        ]

    def chat_completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Send a chat completion request and return the response."""
        client = self._get_client()

        start = time.perf_counter()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        choice = response.choices[0]
        usage = response.usage

        return {
            "text": choice.message.content,
            "model": response.model,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
            "latency_ms": round(elapsed_ms, 2),
            "finish_reason": choice.finish_reason,
        }

    def chat_completion_stream(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> Generator[dict[str, Any], None, None]:
        """Stream a chat completion response."""
        client = self._get_client()

        start = time.perf_counter()
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        first_token = True
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = delta.content if delta else None
            if content is None:
                continue

            now = time.perf_counter()
            result: dict[str, Any] = {
                "token": content,
                "is_first": first_token,
                "is_last": chunk.choices[0].finish_reason is not None,
            }

            if first_token:
                result["ttft_ms"] = round((now - start) * 1000, 2)
                first_token = False

            if result["is_last"]:
                result["generation_time_ms"] = round((now - start) * 1000, 2)

            yield result

    def benchmark_single(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 128,
    ) -> dict[str, Any]:
        """Run a single benchmark request against the OpenAI API."""
        result = self.chat_completion(model, prompt, max_tokens)
        tps = (
            result["completion_tokens"] / (result["latency_ms"] / 1000)
            if result["latency_ms"] > 0 else 0
        )
        return {
            "model": model,
            "tokens_per_second": round(tps, 2),
            "latency_ms": result["latency_ms"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
            "text_preview": result["text"][:200],
        }


# Singleton
openai_client = OpenAIClient()
