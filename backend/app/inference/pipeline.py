"""
ArmPilot-AI — Inference Pipeline
End-to-end inference pipeline with preprocessing, generation, and postprocessing.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Generator, Optional

from app.core.logger import logger
from app.inference.tokenizer import tokenizer_utils
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


class InferencePipeline:
    """End-to-end inference pipeline handling request preprocessing, generation, and response formatting."""

    def __init__(self) -> None:
        self._request_count = 0
        self._total_latency_ms = 0.0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "requests": self._request_count,
            "avg_latency_ms": (
                round(self._total_latency_ms / self._request_count, 2)
                if self._request_count > 0 else 0
            ),
        }

    def run(
        self,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """Execute the full inference pipeline for a non-streaming request."""
        start = time.perf_counter()
        self._request_count += 1

        # Preprocess
        processed = self._preprocess(request)

        # Generate
        from app.services.inference_service import inference_service
        result = inference_service.chat_completion(processed)

        # Postprocess
        result = self._postprocess(result, processed)

        elapsed_ms = (time.perf_counter() - start) * 1000
        self._total_latency_ms += elapsed_ms

        logger.debug(
            "Pipeline completed in %.1fms — tokens=%d",
            elapsed_ms, result.usage.total_tokens,
        )

        return result

    def run_stream(
        self,
        request: ChatCompletionRequest,
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Execute the full inference pipeline for a streaming request."""
        self._request_count += 1

        # Preprocess
        processed = self._preprocess(request)

        # Stream
        from app.services.inference_service import inference_service
        for chunk in inference_service.chat_completion_stream(processed):
            yield chunk

    def _preprocess(self, request: ChatCompletionRequest) -> ChatCompletionRequest:
        """Preprocess the request before generation."""
        # Estimate token count
        messages_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        estimated_tokens = tokenizer_utils.estimate_prompt_tokens(messages_dicts)

        # Truncate if approaching context limit
        if estimated_tokens > 3500:
            logger.warning(
                "Large prompt detected (%d estimated tokens) — truncating",
                estimated_tokens,
            )
            messages = self._truncate_messages(request.messages, max_tokens=3000)
            return request.model_copy(update={"messages": messages})

        return request

    def _postprocess(
        self,
        response: ChatCompletionResponse,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """Postprocess the response after generation."""
        # Apply frequency/presence penalties by filtering repeated tokens
        # (In a production system this would be more sophisticated)

        # Ensure finish reason is set
        for choice in response.choices:
            if not choice.finish_reason:
                choice.finish_reason = "stop"

        return response

    def _truncate_messages(
        self,
        messages: list[ChatMessage],
        max_tokens: int,
    ) -> list[ChatMessage]:
        """Truncate messages to fit within token limits."""
        result: list[ChatMessage] = []
        total_tokens = 0

        # Always keep system message if present
        system_msgs = [m for m in messages if m.role == "system"]
        user_msgs = [m for m in messages if m.role != "system"]

        for msg in system_msgs:
            tokens = tokenizer_utils.count_tokens(msg.content)
            result.append(msg)
            total_tokens += tokens + 4

        # Add as many user/assistant messages as fit
        for msg in reversed(user_msgs):
            tokens = tokenizer_utils.count_tokens(msg.content)
            if total_tokens + tokens > max_tokens:
                # Truncate this message
                remaining = max_tokens - total_tokens
                if remaining > 50:
                    truncated_content = tokenizer_utils.truncate_to_tokens(
                        msg.content, remaining
                    )
                    result.insert(len(system_msgs), ChatMessage(
                        role=msg.role,
                        content=truncated_content,
                    ))
                break
            result.insert(len(system_msgs), msg)
            total_tokens += tokens + 4

        return result

    def estimate_latency(self, request: ChatCompletionRequest) -> dict[str, Any]:
        """Estimate expected latency based on request parameters."""
        messages_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        prompt_tokens = tokenizer_utils.estimate_prompt_tokens(messages_dicts)

        # Rough estimation: ~20ms per token on ARM64 CPU (varies by hardware)
        estimated_generation_ms = request.max_tokens * 20
        estimated_ttft_ms = prompt_tokens * 0.5  # Prompt processing

        return {
            "prompt_tokens_estimate": prompt_tokens,
            "max_tokens": request.max_tokens,
            "estimated_ttft_ms": round(estimated_ttft_ms, 1),
            "estimated_generation_ms": round(estimated_generation_ms, 1),
            "estimated_total_ms": round(estimated_ttft_ms + estimated_generation_ms, 1),
        }


# Singleton
inference_pipeline = InferencePipeline()
