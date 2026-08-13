"""
ArmPilot-AI — Ollama Client
Client for interacting with a local Ollama instance.
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Any, Generator, Optional

from app.core.logger import logger


class OllamaClient:
    """Client for Ollama local inference server."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")

    @property
    def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            self._request("GET", "/api/tags")
            return True
        except (urllib.error.URLError, ConnectionError):
            return False

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Ollama API."""
        url = f"{self._base_url}{path}"
        body = json.dumps(data).encode() if data else None

        req = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"} if body else {},
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def list_models(self) -> list[dict[str, Any]]:
        """List locally available Ollama models."""
        response = self._request("GET", "/api/tags")
        models = response.get("models", [])
        return [
            {
                "name": m.get("name", ""),
                "size": m.get("size", 0),
                "size_mb": round(m.get("size", 0) / (1024 ** 2), 1),
                "modified_at": m.get("modified_at", ""),
                "digest": m.get("digest", ""),
            }
            for m in models
        ]

    def pull_model(self, model_name: str) -> dict[str, Any]:
        """Pull (download) a model from Ollama."""
        logger.info("Pulling Ollama model: %s", model_name)
        start = time.perf_counter()

        response = self._request(
            "POST",
            "/api/pull",
            data={"name": model_name},
            timeout=300.0,
        )

        elapsed = time.perf_counter() - start
        logger.info("Model %s pulled in %.1fs", model_name, elapsed)

        return {
            "model": model_name,
            "status": response.get("status", ""),
            "pull_time_seconds": round(elapsed, 1),
        }

    def delete_model(self, model_name: str) -> bool:
        """Delete a locally pulled model."""
        try:
            self._request("DELETE", "/api/delete", data={"name": model_name})
            logger.info("Deleted Ollama model: %s", model_name)
            return True
        except Exception as e:
            logger.error("Failed to delete model %s: %s", model_name, e)
            return False

    def generate(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Generate text using Ollama."""
        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        start = time.perf_counter()
        response = self._request("POST", "/api/generate", data=data)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "text": response.get("response", ""),
            "model": response.get("model", model),
            "total_duration_ms": round(elapsed_ms, 2),
            "eval_count": response.get("eval_count", 0),
            "eval_duration_ms": response.get("eval_duration", 0) / 1_000_000,
            "done": response.get("done", True),
        }

    def generate_stream(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> Generator[dict[str, Any], None, None]:
        """Stream text generation from Ollama."""
        url = f"{self._base_url}/api/generate"
        body = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }).encode()

        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        start = time.perf_counter()
        first_token = True

        with urllib.request.urlopen(req, timeout=60.0) as resp:
            for line in resp:
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line.decode())
                except json.JSONDecodeError:
                    continue

                text = chunk.get("response", "")
                done = chunk.get("done", False)

                now = time.perf_counter()
                result: dict[str, Any] = {
                    "token": text,
                    "is_first": first_token,
                    "is_last": done,
                }

                if first_token:
                    result["ttft_ms"] = round((now - start) * 1000, 2)
                    first_token = False

                if done:
                    result["total_tokens"] = chunk.get("eval_count", 0)
                    result["generation_time_ms"] = round((now - start) * 1000, 2)

                yield result

    def benchmark(
        self,
        model: str,
        prompt: str,
        num_requests: int = 10,
        max_tokens: int = 128,
    ) -> dict[str, Any]:
        """Run a simple benchmark against a local Ollama model."""
        latencies: list[float] = []
        total_tokens = 0

        # Warmup
        self.generate(model, prompt, max_tokens=max_tokens, temperature=0.7)

        for _ in range(num_requests):
            start = time.perf_counter()
            result = self.generate(model, prompt, max_tokens=max_tokens, temperature=0.7)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
            total_tokens += result.get("eval_count", 0)

        latencies.sort()
        avg_latency = sum(latencies) / len(latencies)
        total_time = sum(latencies) / 1000

        return {
            "model": model,
            "num_requests": num_requests,
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": round(latencies[0], 2),
            "max_latency_ms": round(latencies[-1], 2),
            "p95_latency_ms": round(latencies[int(len(latencies) * 0.95)], 2),
            "total_tokens": total_tokens,
            "tokens_per_second": round(total_tokens / total_time, 2) if total_time > 0 else 0,
            "requests_per_second": round(num_requests / total_time, 2) if total_time > 0 else 0,
        }


# Singleton
ollama_client = OllamaClient()
