"""
ArmPilot-AI — Inference Schemas
OpenAI-compatible request/response models.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── OpenAI-Compatible Request ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model ID to use")
    messages: list[ChatMessage] = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=256, ge=1, le=4096)
    stream: bool = Field(default=False)
    stop: Optional[list[str]] = None
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


# ── OpenAI-Compatible Response ────────────────────────────────────────────────

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: UsageInfo


# ── Streaming ─────────────────────────────────────────────────────────────────

class ChatCompletionChunkDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]


# ── Model Info ────────────────────────────────────────────────────────────────

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    name: str
    provider: str = "local"
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    size_mb: Optional[float] = None
    context_length: int = 2048
    runtime: str = "llama.cpp"
    file_path: Optional[str] = None
    loaded: bool = False


class ModelListResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]
