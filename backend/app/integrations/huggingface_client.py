"""
ArmPilot-AI — HuggingFace Client
Client for downloading models and fetching metadata from the HuggingFace Hub.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings
from app.core.logger import logger


class HuggingFaceClient:
    """Client for interacting with HuggingFace Hub."""

    def __init__(self, token: Optional[str] = None) -> None:
        self._token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")

    @property
    def is_configured(self) -> bool:
        return bool(self._token)

    def _get_api(self) -> Any:
        """Get the HuggingFace API client."""
        try:
            from huggingface_hub import HfApi
        except ImportError:
            raise RuntimeError(
                "huggingface_hub is not installed. "
                "Install with: pip install huggingface_hub"
            )
        kwargs: dict[str, Any] = {}
        if self._token:
            kwargs["token"] = self._token
        return HfApi(**kwargs)

    def search_models(
        self,
        query: str = "",
        limit: int = 20,
        sort: str = "downloads",
    ) -> list[dict[str, Any]]:
        """Search for models on HuggingFace Hub."""
        api = self._get_api()

        models = api.list_models(
            search=query,
            limit=limit,
            sort=sort,
            direction=-1,
            filter="gguf",
        )

        results: list[dict[str, Any]] = []
        for model in models:
            results.append({
                "id": model.id,
                "author": model.author,
                "downloads": model.downloads,
                "likes": model.likes,
                "tags": model.tags or [],
                "pipeline_tag": getattr(model, "pipeline_tag", None),
                "created_at": getattr(model, "createdAt", None),
            })

        return results

    def get_model_info(self, model_id: str) -> dict[str, Any]:
        """Get detailed information about a specific model."""
        api = self._get_api()

        model_info = api.model_info(model_id)

        siblings = getattr(model_info, "siblings", None) or []
        gguf_files = [
            {
                "filename": s.rfilename,
                "size_mb": round(s.size / (1024 ** 2), 1) if s.size else None,
            }
            for s in siblings
            if hasattr(s, "rfilename") and ".gguf" in (s.rfilename or "")
        ]

        return {
            "id": model_info.id,
            "author": getattr(model_info, "author", None),
            "downloads": getattr(model_info, "downloads", 0),
            "likes": getattr(model_info, "likes", 0),
            "tags": getattr(model_info, "tags", []),
            "pipeline_tag": getattr(model_info, "pipeline_tag", None),
            "gguf_files": gguf_files,
            "model_card": getattr(model_info, "card_data", None),
        }

    def download_gguf(
        self,
        model_id: str,
        filename: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> str:
        """Download a GGUF model file. Returns the local path."""
        try:
            from huggingface_hub import hf_hub_download
        except ImportError:
            raise RuntimeError(
                "huggingface_hub is not installed. "
                "Install with: pip install huggingface_hub"
            )

        dest_dir = Path(destination) if destination else settings.resolve_path(settings.models_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        kwargs: dict[str, Any] = {
            "repo_id": model_id,
            "local_dir": str(dest_dir),
        }
        if filename:
            kwargs["filename"] = filename
        if self._token:
            kwargs["token"] = self._token

        logger.info("Downloading model %s from HuggingFace...", model_id)
        path = hf_hub_download(**kwargs)
        logger.info("Downloaded to: %s", path)

        return str(path)


# Singleton
huggingface_client = HuggingFaceClient()
