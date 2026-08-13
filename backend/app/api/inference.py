"""
ArmPilot-AI — Inference API
OpenAI-compatible chat completions + model management.
"""

from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelListResponse,
)
from app.services.inference_service import inference_service
from app.core.exceptions import ArmPilotError

router = APIRouter()


# ── OpenAI-Compatible Endpoints ───────────────────────────────────────────────

@router.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)."""
    models = inference_service.list_models()
    return ModelListResponse(data=models)


@router.post("/v1/models/{model_id}/load")
async def load_model(model_id: str, n_threads: int = 4, n_ctx: int = 2048, n_batch: int = 512):
    """Load a model for inference."""
    model = inference_service.load_model(
        model_id,
        n_threads=n_threads,
        n_ctx=n_ctx,
        n_batch=n_batch,
    )
    return {"success": True, "model": model.model_dump()}


@router.post("/v1/models/unload")
async def unload_model():
    """Unload the current model."""
    inference_service.unload()
    return {"success": True, "message": "Model unloaded"}


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    Supports both streaming and non-streaming.
    """
    if request.stream:
        return StreamingResponse(
            _stream_response(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        response = inference_service.chat_completion(request)
        return response


async def _stream_response(request: ChatCompletionRequest):
    """Generate SSE stream for chat completions."""
    try:
        for chunk in inference_service.chat_completion_stream(request):
            data = chunk.model_dump_json()
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"
    except ArmPilotError:
        raise
    except Exception as e:
        error_data = json.dumps({"error": str(e)})
        yield f"data: {error_data}\n\n"


@router.get("/v1/models/status")
async def model_status():
    """Get current model/inference status."""
    return {"success": True, **inference_service.get_status()}
