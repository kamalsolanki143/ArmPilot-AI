"""
ArmPilot-AI — Text Generation
High-level text generation with prompt management and response formatting.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Generator, Optional

from app.core.logger import logger
from app.schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatMessage,
    UsageInfo,
)


class TextGenerator:
    """High-level text generation interface wrapping the inference runtime."""

    def __init__(self) -> None:
        self._generation_count = 0
        self._total_tokens = 0
        self._total_latency_ms = 0.0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "generations": self._generation_count,
            "total_tokens": self._total_tokens,
            "avg_latency_ms": (
                round(self._total_latency_ms / self._generation_count, 2)
                if self._generation_count > 0 else 0
            ),
        }

    def generate(
        self,
        prompt: str,
        model: str = "default",
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[list[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a complete response from a prompt."""
        from app.services.inference_service import inference_service

        full_prompt = self._build_prompt(prompt, system_prompt)

        start = time.perf_counter()
        result = inference_service.runtime.generate(
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        self._generation_count += 1
        self._total_tokens += result.get("completion_tokens", 0)
        self._total_latency_ms += elapsed_ms

        return {
            "text": result["text"],
            "model": model,
            "prompt_tokens": result.get("prompt_tokens", 0),
            "completion_tokens": result.get("completion_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
            "generation_time_ms": round(elapsed_ms, 2),
            "tokens_per_second": result.get("tokens_per_second", 0),
        }

    def generate_stream(
        self,
        prompt: str,
        model: str = "default",
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[list[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Generate a streaming response from a prompt."""
        from app.services.inference_service import inference_service

        full_prompt = self._build_prompt(prompt, system_prompt)

        for token_data in inference_service.runtime.generate_stream(
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
        ):
            yield token_data

    def generate_chat(
        self,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """Generate a chat completion response."""
        from app.services.inference_service import inference_service

        result = inference_service.chat_completion(request)

        self._generation_count += 1
        self._total_tokens += result.usage.total_tokens

        return result

    def generate_chat_stream(
        self,
        request: ChatCompletionRequest,
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Generate a streaming chat completion response."""
        from app.services.inference_service import inference_service

        for chunk in inference_service.chat_completion_stream(request):
            yield chunk

    def format_response(
        self,
        text: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> ChatCompletionResponse:
        """Format raw text into an OpenAI-compatible response."""
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=text),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    @staticmethod
    def _build_prompt(
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Build a formatted prompt from user and optional system prompts."""
        parts: list[str] = []
        if system_prompt:
            parts.append(f"<|system|>\n{system_prompt}</s>")
        parts.append(f"<|user|>\n{user_prompt}</s>")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)


# Singleton
text_generator = TextGenerator()
