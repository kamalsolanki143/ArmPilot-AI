"""
ArmPilot-AI — Model Loader
Discovers GGUF model files and manages model registry.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.core.logger import logger
from app.schemas.inference import ModelInfo


# Known model metadata for common models (used to enrich discovered models)
_KNOWN_MODELS: dict[str, dict] = {
    "tinyllama": {"name": "TinyLlama 1.1B", "provider": "TinyLlama", "parameters": "1.1B"},
    "llama-3": {"name": "Llama 3", "provider": "Meta", "parameters": "8B"},
    "llama-3.2": {"name": "Llama 3.2", "provider": "Meta"},
    "mistral": {"name": "Mistral", "provider": "Mistral AI"},
    "phi-3": {"name": "Phi-3 Mini", "provider": "Microsoft", "parameters": "3.8B"},
    "phi-2": {"name": "Phi-2", "provider": "Microsoft", "parameters": "2.7B"},
    "gemma": {"name": "Gemma", "provider": "Google"},
    "qwen": {"name": "Qwen", "provider": "Alibaba"},
    "smollm": {"name": "SmolLM", "provider": "HuggingFace"},
}


def _infer_quantization(filename: str) -> str | None:
    """Infer quantization from filename (e.g., model-Q4_K_M.gguf -> Q4_K_M)."""
    name = filename.upper()
    for q in ["Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L", "Q4_0", "Q4_K_S", "Q4_K_M",
              "Q5_0", "Q5_K_S", "Q5_K_M", "Q6_K", "Q8_0", "F16", "F32"]:
        if q in name:
            return q
    return None


def _match_known_model(filename: str) -> dict:
    """Match filename against known model metadata."""
    lower = filename.lower()
    for key, meta in _KNOWN_MODELS.items():
        if key in lower:
            return meta
    return {}


def discover_models() -> list[ModelInfo]:
    """Scan the models directory for GGUF files and return model info list."""
    models_dir = settings.resolve_path(settings.models_dir)
    models: list[ModelInfo] = []

    if not models_dir.exists():
        logger.warning("Models directory does not exist: %s", models_dir)
        return models

    for path in sorted(models_dir.rglob("*.gguf")):
        model_id = path.stem.lower().replace(" ", "-")
        size_mb = round(path.stat().st_size / (1024 ** 2), 1)
        quant = _infer_quantization(path.name)
        meta = _match_known_model(path.name)

        models.append(ModelInfo(
            id=model_id,
            name=meta.get("name", path.stem),
            provider=meta.get("provider", "Unknown"),
            parameters=meta.get("parameters"),
            quantization=quant,
            size_mb=size_mb,
            context_length=settings.default_context_length,
            runtime="llama.cpp",
            file_path=str(path),
            loaded=False,
        ))

    logger.info("Discovered %d model(s) in %s", len(models), models_dir)
    return models


def find_model(model_id: str, models: list[ModelInfo] | None = None) -> ModelInfo | None:
    """Find a model by its ID."""
    if models is None:
        models = discover_models()
    for m in models:
        if m.id == model_id:
            return m
    return None
