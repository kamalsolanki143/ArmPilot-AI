"""
ArmPilot-AI — Inference Service Tests
Tests for the inference service: model loading, chat completion, streaming.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import InferenceError, ModelNotLoadedError, ModelNotFoundError
from app.schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ModelInfo,
)


# ── Model Listing Tests ───────────────────────────────────────────────────────

class TestListModels:
    """Tests for listing available models."""

    @patch("app.services.inference_service.discover_models")
    def test_list_models_returns_list(self, mock_discover: MagicMock):
        from app.services.inference_service import InferenceService
        mock_discover.return_value = []
        svc = InferenceService()
        result = svc.list_models()
        assert isinstance(result, list)

    @patch("app.services.inference_service.discover_models")
    def test_list_models_populates_cache(self, mock_discover: MagicMock):
        from app.services.inference_service import InferenceService
        mock_discover.return_value = [
            ModelInfo(id="model-1", name="Model 1"),
        ]
        svc = InferenceService()
        svc.list_models()
        assert len(svc._models_cache) == 1

    @patch("app.services.inference_service.discover_models")
    def test_list_models_marks_loaded(self, mock_discover: MagicMock):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        svc.current_model = ModelInfo(id="model-1", name="Model 1", loaded=True)
        mock_discover.return_value = [
            ModelInfo(id="model-1", name="Model 1"),
        ]
        result = svc.list_models()
        assert result[0].loaded is True


# ── Model Loading Tests ───────────────────────────────────────────────────────

class TestLoadModel:
    """Tests for model loading."""

    @patch("app.services.inference_service.find_model")
    @patch("app.services.inference_service.discover_models")
    def test_load_model_not_found_raises(self, mock_discover: MagicMock, mock_find: MagicMock):
        from app.services.inference_service import InferenceService
        mock_discover.return_value = []
        mock_find.return_value = None
        svc = InferenceService()
        with pytest.raises(ModelNotFoundError):
            svc.load_model("nonexistent-model")

    @patch("app.services.inference_service.find_model")
    @patch("app.services.inference_service.get_runtime")
    def test_load_model_already_loaded(self, mock_get_runtime: MagicMock, mock_find: MagicMock):
        from app.services.inference_service import InferenceService
        model = ModelInfo(id="model-1", name="Model 1")
        mock_find.return_value = model
        svc = InferenceService()
        svc.current_model = ModelInfo(id="model-1", name="Model 1")
        svc.runtime = MagicMock()
        svc.runtime.is_loaded.return_value = True
        result = svc.load_model("model-1")
        assert result.id == "model-1"

    @patch("app.services.inference_service.find_model")
    @patch("app.services.inference_service.discover_models")
    @patch("app.services.inference_service.get_runtime")
    def test_load_model_success(
        self, mock_get_runtime: MagicMock, mock_discover: MagicMock,
        mock_find: MagicMock,
    ):
        from app.services.inference_service import InferenceService
        model = ModelInfo(id="model-1", name="Model 1", file_path="/path/to/model.gguf")
        mock_discover.return_value = [model]
        mock_find.return_value = model
        mock_runtime = MagicMock()
        mock_get_runtime.return_value = mock_runtime
        svc = InferenceService()
        result = svc.load_model("model-1")
        assert result.loaded is True
        mock_runtime.load_model.assert_called_once()

    @patch("app.services.inference_service.find_model")
    @patch("app.services.inference_service.discover_models")
    @patch("app.services.inference_service.get_runtime")
    def test_load_model_unloads_previous(
        self, mock_get_runtime: MagicMock, mock_discover: MagicMock,
        mock_find: MagicMock,
    ):
        from app.services.inference_service import InferenceService
        old_model = ModelInfo(id="old-model", name="Old", file_path="/old.gguf")
        new_model = ModelInfo(id="new-model", name="New", file_path="/new.gguf")
        mock_discover.return_value = [old_model, new_model]
        mock_find.return_value = new_model
        old_runtime = MagicMock()
        mock_runtime = MagicMock()
        mock_get_runtime.return_value = mock_runtime

        svc = InferenceService()
        svc.runtime = old_runtime
        svc.current_model = old_model
        svc.load_model("new-model")
        old_runtime.unload_model.assert_called_once()


# ── Model Unloading Tests ─────────────────────────────────────────────────────

class TestUnloadModel:
    """Tests for model unloading."""

    def test_unload_clears_state(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        svc.runtime = MagicMock()
        svc.current_model = ModelInfo(id="model-1", name="M1")
        svc.unload()
        assert svc.runtime is None
        assert svc.current_model is None

    def test_unload_when_nothing_loaded(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        svc.unload()
        assert svc.runtime is None


# ── Prompt Building Tests ─────────────────────────────────────────────────────

class TestBuildPrompt:
    """Tests for chat message to prompt conversion."""

    def test_build_prompt_system_user_assistant(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        messages = [
            ChatMessage(role="system", content="You are helpful."),
            ChatMessage(role="user", content="Hello!"),
            ChatMessage(role="assistant", content="Hi there!"),
        ]
        prompt = svc._build_prompt(messages)
        assert "<|system|>" in prompt
        assert "<|user|>" in prompt
        assert "<|assistant|>" in prompt
        assert "You are helpful." in prompt
        assert "Hello!" in prompt
        assert "Hi there!" in prompt

    def test_build_prompt_ends_with_assistant(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        messages = [ChatMessage(role="user", content="Hello")]
        prompt = svc._build_prompt(messages)
        assert prompt.endswith("<|assistant|>\n")

    def test_build_prompt_user_only(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        messages = [ChatMessage(role="user", content="Test")]
        prompt = svc._build_prompt(messages)
        assert "<|user|>" in prompt
        assert "Test" in prompt


# ── Chat Completion Tests ─────────────────────────────────────────────────────

class TestChatCompletion:
    """Tests for non-streaming chat completion."""

    def test_chat_completion_no_model_raises(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        req = ChatCompletionRequest(
            model="test",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        with pytest.raises(ModelNotLoadedError):
            svc.chat_completion(req)

    def test_chat_completion_success(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate.return_value = {
            "text": "Hello! How can I help?",
            "prompt_tokens": 5,
            "completion_tokens": 6,
            "total_tokens": 11,
        }
        svc.runtime = mock_runtime
        req = ChatCompletionRequest(
            model="test",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        response = svc.chat_completion(req)
        assert isinstance(response, ChatCompletionResponse)
        assert response.model == "test"
        assert len(response.choices) == 1
        assert response.choices[0].message.role == "assistant"
        assert response.usage.total_tokens == 11

    def test_chat_completion_passes_parameters(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate.return_value = {
            "text": "response", "prompt_tokens": 1,
            "completion_tokens": 1, "total_tokens": 2,
        }
        svc.runtime = mock_runtime
        req = ChatCompletionRequest(
            model="test",
            messages=[ChatMessage(role="user", content="Hi")],
            max_tokens=64,
            temperature=0.5,
            top_p=0.8,
            stop=["END"],
        )
        svc.chat_completion(req)
        mock_runtime.generate.assert_called_once_with(
            prompt=mock_runtime.generate.call_args.kwargs["prompt"],
            max_tokens=64,
            temperature=0.5,
            top_p=0.8,
            stop=["END"],
        )

    def test_chat_completion_error_raises(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate.side_effect = RuntimeError("OOM")
        svc.runtime = mock_runtime
        req = ChatCompletionRequest(
            model="test",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        with pytest.raises(InferenceError):
            svc.chat_completion(req)


# ── Streaming Tests ───────────────────────────────────────────────────────────

class TestChatCompletionStream:
    """Tests for streaming chat completion."""

    def test_stream_no_model_raises(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        req = ChatCompletionRequest(
            model="test",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        with pytest.raises(ModelNotLoadedError):
            list(svc.chat_completion_stream(req))

    def test_stream_yields_chunks(self):
        from app.services.inference_service import InferenceService
        from app.schemas.inference import ChatCompletionChunk
        svc = InferenceService()
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate_stream.return_value = iter([
            {"token": "Hello", "is_first": True, "is_last": False, "ttft_ms": 50.0},
            {"token": " World", "is_first": False, "is_last": True,
             "total_tokens": 2, "generation_time_ms": 200.0, "tokens_per_second": 10.0},
        ])
        svc.runtime = mock_runtime
        req = ChatCompletionRequest(
            model="test",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        chunks = list(svc.chat_completion_stream(req))
        assert len(chunks) >= 2
        assert all(isinstance(c, ChatCompletionChunk) for c in chunks)
        # First chunk should have role
        assert chunks[0].choices[0].delta.role == "assistant"
        # Last chunk should have finish_reason
        assert chunks[-1].choices[0].finish_reason == "stop"

    def test_stream_error_raises(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.generate_stream.side_effect = RuntimeError("GPU OOM")
        svc.runtime = mock_runtime
        req = ChatCompletionRequest(
            model="test",
            messages=[ChatMessage(role="user", content="Hello")],
        )
        with pytest.raises(InferenceError):
            list(svc.chat_completion_stream(req))


# ── Status Tests ──────────────────────────────────────────────────────────────

class TestGetStatus:
    """Tests for inference status endpoint."""

    def test_status_no_model(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        status = svc.get_status()
        assert status["model_loaded"] is False
        assert status["current_model"] is None

    def test_status_with_model(self):
        from app.services.inference_service import InferenceService
        svc = InferenceService()
        mock_runtime = MagicMock()
        mock_runtime.is_loaded.return_value = True
        mock_runtime.name = "llama.cpp"
        mock_runtime.get_model_info.return_value = {"path": "/test.gguf"}
        svc.runtime = mock_runtime
        svc.current_model = ModelInfo(id="m1", name="Model 1")
        status = svc.get_status()
        assert status["model_loaded"] is True
        assert status["runtime"] == "llama.cpp"
