"""
ArmPilot-AI — Inference Service
Central service managing model lifecycle and inference requests.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Generator, Optional

from app.core.config import settings
from app.core.exceptions import ModelNotLoadedError, ModelNotFoundError, InferenceError
from app.core.logger import logger
from app.inference.runtime import InferenceRuntime, get_runtime
from app.inference.loader import discover_models, find_model
from app.schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatMessage,
    ModelInfo,
    UsageInfo,
)


class InferenceService:
    """Manages the active inference runtime and processes chat requests."""

    def __init__(self) -> None:
        self.runtime: Optional[InferenceRuntime] = None
        self.current_model: Optional[ModelInfo] = None
        self._models_cache: list[ModelInfo] = []

    def list_models(self) -> list[ModelInfo]:
        """List all available models."""
        self._models_cache = discover_models()
        # Update loaded state
        for m in self._models_cache:
            m.loaded = (
                self.current_model is not None
                and m.id == self.current_model.id
            )
        return self._models_cache

    def load_model(self, model_id: str, **kwargs: Any) -> ModelInfo:
        """Load a model by its ID."""
        model = find_model(model_id, self._models_cache or None)
        if model is None:
            # Refresh cache and try again
            self._models_cache = discover_models()
            model = find_model(model_id, self._models_cache)
        if model is None:
            raise ModelNotFoundError(model_id)

        # Unload current model if different
        if self.runtime is not None and self.current_model and self.current_model.id != model_id:
            self.unload()

        if self.runtime is not None and self.current_model and self.current_model.id == model_id:
            logger.info("Model %s already loaded", model_id)
            return self.current_model

        # Create runtime and load
        runtime = get_runtime(model.runtime)
        runtime.load_model(
            model.file_path,
            n_ctx=kwargs.get("n_ctx", settings.default_context_length),
            n_threads=kwargs.get("n_threads", settings.default_threads),
            n_batch=kwargs.get("n_batch", settings.default_batch_size),
            n_gpu_layers=kwargs.get("n_gpu_layers", settings.gpu_layers),
        )

        self.runtime = runtime
        self.current_model = model
        self.current_model.loaded = True

        logger.info("Model %s loaded successfully", model_id)
        return self.current_model

    def unload(self) -> None:
        """Unload the current model."""
        if self.runtime is not None:
            self.runtime.unload_model()
            self.runtime = None
        if self.current_model is not None:
            self.current_model.loaded = False
            self.current_model = None
        logger.info("Model unloaded")

    def _build_prompt(self, messages: list[ChatMessage]) -> str:
        """Convert chat messages to a prompt string for the model."""
        parts: list[str] = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"<|system|>\n{msg.content}</s>")
            elif msg.role == "user":
                parts.append(f"<|user|>\n{msg.content}</s>")
            elif msg.role == "assistant":
                parts.append(f"<|assistant|>\n{msg.content}</s>")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)

    def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Process a non-streaming chat completion request."""
        if self.runtime is None or not self.runtime.is_loaded():
            raise ModelNotLoadedError()

        prompt = self._build_prompt(request.messages)

        try:
            result = self.runtime.generate(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop,
            )
        except Exception as e:
            raise InferenceError(str(e))

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=result["text"]),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(
                prompt_tokens=result.get("prompt_tokens", 0),
                completion_tokens=result.get("completion_tokens", 0),
                total_tokens=result.get("total_tokens", 0),
            ),
        )

    def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> Generator[ChatCompletionChunk, None, None]:
        """Process a streaming chat completion request."""
        if self.runtime is None or not self.runtime.is_loaded():
            raise ModelNotLoadedError()

        prompt = self._build_prompt(request.messages)
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        try:
            stream = self.runtime.generate_stream(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop,
            )

            # First chunk with role
            yield ChatCompletionChunk(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionChunkDelta(role="assistant"),
                    )
                ],
            )

            for token_data in stream:
                finish = "stop" if token_data.get("is_last") else None
                yield ChatCompletionChunk(
                    id=completion_id,
                    created=created,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0,
                            delta=ChatCompletionChunkDelta(content=token_data["token"]),
                            finish_reason=finish,
                        )
                    ],
                )

        except Exception as e:
            raise InferenceError(str(e))

    def get_status(self) -> dict[str, Any]:
        """Get current inference service status."""
        return {
            "model_loaded": self.runtime is not None and self.runtime.is_loaded(),
            "current_model": self.current_model.model_dump() if self.current_model else None,
            "runtime": self.runtime.name if self.runtime else None,
            "model_info": self.runtime.get_model_info() if self.runtime and self.runtime.is_loaded() else None,
        }


# Singleton instance
inference_service = InferenceService()
