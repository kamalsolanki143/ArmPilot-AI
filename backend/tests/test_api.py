"""
ArmPilot-AI — API Endpoint Tests
Tests for all FastAPI API endpoints.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Health Endpoint Tests ──────────────────────────────────────────────────────

class TestHealthEndpoint:
    """Tests for /health endpoint."""

    @patch("app.api.health.get_hardware_info")
    @patch("app.api.health.inference_service")
    def test_health_check_returns_200(
        self, mock_inference: MagicMock, mock_hw: MagicMock, client: TestClient
    ):
        mock_hw.return_value = {
            "architecture": "ARM64",
            "is_arm64": True,
        }
        mock_inference.get_status.return_value = {
            "model_loaded": False,
            "current_model": None,
        }
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch("app.api.health.get_hardware_info")
    @patch("app.api.health.inference_service")
    def test_health_check_includes_version(
        self, mock_inference: MagicMock, mock_hw: MagicMock, client: TestClient
    ):
        mock_hw.return_value = {"architecture": "X86_64", "is_arm64": False}
        mock_inference.get_status.return_value = {
            "model_loaded": False,
            "current_model": None,
        }
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert "app" in data


# ── Metrics Endpoint Tests ─────────────────────────────────────────────────────

class TestMetricsEndpoint:
    """Tests for /api/metrics endpoint."""

    @patch("app.api.health.get_hardware_info")
    @patch("app.api.health.get_system_metrics")
    @patch("app.api.health.inference_service")
    def test_metrics_returns_success(
        self, mock_inference: MagicMock, mock_sys: MagicMock,
        mock_hw: MagicMock, client: TestClient
    ):
        mock_hw.return_value = {"architecture": "ARM64"}
        mock_sys.return_value = {"cpu_utilization_percent": 50.0}
        mock_inference.get_status.return_value = {"model_loaded": False}
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "hardware" in data
        assert "system" in data
        assert "inference" in data


# ── Inference Endpoint Tests ──────────────────────────────────────────────────

class TestInferenceEndpoints:
    """Tests for /v1/* inference endpoints."""

    @patch("app.api.inference.inference_service")
    def test_list_models(self, mock_service: MagicMock, client: TestClient):
        mock_service.list_models.return_value = []
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert isinstance(data["data"], list)

    @patch("app.api.inference.inference_service")
    def test_list_models_returns_models(self, mock_service: MagicMock, client: TestClient):
        mock_service.list_models.return_value = [
            MagicMock(id="model-1", name="Test Model", model_dump=MagicMock(return_value={
                "id": "model-1", "name": "Test Model", "object": "model",
            })),
        ]
        response = client.get("/v1/models")
        assert response.status_code == 200

    @patch("app.api.inference.inference_service")
    def test_model_status(self, mock_service: MagicMock, client: TestClient):
        mock_service.get_status.return_value = {
            "model_loaded": False,
            "current_model": None,
            "runtime": None,
            "model_info": None,
        }
        response = client.get("/v1/models/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("app.api.inference.inference_service")
    def test_chat_completions(self, mock_service: MagicMock, client: TestClient):
        from app.schemas.inference import (
            ChatCompletionResponse, ChatCompletionChoice,
            ChatMessage, UsageInfo,
        )
        mock_service.chat_completion.return_value = ChatCompletionResponse(
            id="chatcmpl-test",
            created=int(datetime.now(timezone.utc).timestamp()),
            model="test-model",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="Hello!"),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(prompt_tokens=5, completion_tokens=3, total_tokens=8),
        )
        response = client.post("/v1/chat/completions", json={
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert len(data["choices"]) == 1

    @patch("app.api.inference.inference_service")
    def test_chat_completions_missing_messages(self, mock_service: MagicMock, client: TestClient):
        response = client.post("/v1/chat/completions", json={
            "model": "test-model",
        })
        assert response.status_code == 422

    @patch("app.api.inference.inference_service")
    def test_chat_completions_empty_messages(self, mock_service: MagicMock, client: TestClient):
        response = client.post("/v1/chat/completions", json={
            "model": "test-model",
            "messages": [],
        })
        assert response.status_code == 422

    @patch("app.api.inference.inference_service")
    def test_load_model(self, mock_service: MagicMock, client: TestClient):
        mock_service.load_model.return_value = MagicMock(
            model_dump=MagicMock(return_value={"id": "test-model", "loaded": True})
        )
        response = client.post("/v1/models/test-model/load")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("app.api.inference.inference_service")
    def test_unload_model(self, mock_service: MagicMock, client: TestClient):
        response = client.post("/v1/models/unload")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_service.unload.assert_called_once()


# ── Benchmark Endpoint Tests ──────────────────────────────────────────────────

class TestBenchmarkEndpoints:
    """Tests for /api/benchmark/* endpoints."""

    @patch("app.api.benchmark.storage")
    def test_list_benchmarks_empty(self, mock_storage: MagicMock, client: TestClient):
        mock_storage.list_benchmarks.return_value = []
        response = client.get("/api/benchmarks")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 0

    @patch("app.api.benchmark.storage")
    def test_get_benchmark_not_found(self, mock_storage: MagicMock, client: TestClient):
        mock_storage.get_benchmark.return_value = None
        response = client.get("/api/benchmark/nonexistent")
        assert response.status_code == 404

    @patch("app.api.benchmark.storage")
    def test_get_latest_benchmark_empty(self, mock_storage: MagicMock, client: TestClient):
        mock_storage.list_benchmarks.return_value = []
        response = client.get("/api/benchmark/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is None


# ── Optimization Endpoint Tests ───────────────────────────────────────────────

class TestOptimizationEndpoints:
    """Tests for /api/optimization/* endpoints."""

    @patch("app.api.optimization.storage")
    def test_list_optimizations_empty(self, mock_storage: MagicMock, client: TestClient):
        mock_storage.list_optimizations.return_value = []
        response = client.get("/api/optimizations")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 0

    @patch("app.api.optimization.storage")
    def test_get_optimization_not_found(self, mock_storage: MagicMock, client: TestClient):
        mock_storage.get_optimization.return_value = None
        response = client.get("/api/optimization/nonexistent")
        assert response.status_code == 404


# ── Recommendation Endpoint Tests ─────────────────────────────────────────────

class TestRecommendationEndpoints:
    """Tests for /api/recommendations endpoint."""

    @patch("app.api.recommendation.storage")
    @patch("app.api.recommendation.recommendation_engine")
    def test_generate_recommendations_without_benchmark(
        self, mock_engine: MagicMock, mock_storage: MagicMock, client: TestClient
    ):
        mock_engine.analyze.return_value = []
        response = client.post("/api/recommendations", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["recommendations"], list)

    @patch("app.api.recommendation.storage")
    def test_generate_recommendations_benchmark_not_found(
        self, mock_storage: MagicMock, client: TestClient
    ):
        mock_storage.get_benchmark.return_value = None
        response = client.post("/api/recommendations", json={
            "benchmark_id": "nonexistent",
        })
        assert response.status_code == 404


# ── Reports Endpoint Tests ────────────────────────────────────────────────────

class TestReportEndpoints:
    """Tests for /api/reports/* endpoints."""

    @patch("app.api.reports.storage")
    def test_list_reports_empty(self, mock_storage: MagicMock, client: TestClient):
        mock_storage.list_reports.return_value = []
        response = client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 0

    @patch("app.api.reports.storage")
    def test_get_report_not_found(self, mock_storage: MagicMock, client: TestClient):
        mock_storage.get_report.return_value = None
        response = client.get("/api/reports/nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @patch("app.api.reports.storage")
    @patch("app.api.reports.generate_benchmark_report")
    def test_generate_report_from_benchmark(
        self, mock_gen: MagicMock, mock_storage: MagicMock, client: TestClient
    ):
        from app.schemas.benchmark import BenchmarkResult, BenchmarkConfig, LatencyMetrics
        mock_storage.get_benchmark.return_value = {
            "id": "bench-001",
            "status": "completed",
            "config": {"model": "test", "batch_size": 512, "threads": 4,
                       "num_requests": 10, "max_tokens": 128, "runtime": "llama.cpp",
                       "concurrency": 1, "duration_seconds": 60, "warmup_requests": 3,
                       "prompt": "test"},
            "timestamp": "",
            "latency": {},
        }
        mock_gen.return_value = "# Report\nTest content"
        response = client.post("/api/reports/generate", json={
            "benchmark_id": "bench-001",
            "format": "markdown",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ── Auth Endpoint Tests ───────────────────────────────────────────────────────

class TestAuthEndpoints:
    """Tests for /auth/* endpoints."""

    @patch("app.api.auth.auth_service")
    def test_register(self, mock_auth: MagicMock, client: TestClient):
        mock_auth.register.return_value = (
            MagicMock(id="user-1", email="test@test.com", username="test",
                      full_name="", role=MagicMock(value="user"),
                      is_active=True, is_verified=False,
                      created_at=datetime.now(timezone.utc)),
            MagicMock(access_token="token", refresh_token="refresh",
                      token_type="bearer", expires_in=3600),
        )
        mock_auth.to_user_info.return_value = MagicMock(
            id="user-1", email="test@test.com", username="test",
            full_name="", role=MagicMock(value="user"),
            is_active=True, is_verified=False,
            created_at=datetime.now(timezone.utc),
        )
        response = client.post("/auth/register", json={
            "email": "test@test.com",
            "username": "test",
            "password": "password123",
        })
        assert response.status_code in (201, 200, 409)

    @patch("app.api.auth.auth_service")
    def test_register_duplicate_email(self, mock_auth: MagicMock, client: TestClient):
        mock_auth.register.side_effect = ValueError("Email already registered")
        response = client.post("/auth/register", json={
            "email": "existing@test.com",
            "username": "newuser",
            "password": "password123",
        })
        assert response.status_code == 409

    @patch("app.api.auth.auth_service")
    def test_login_success(self, mock_auth: MagicMock, client: TestClient):
        mock_auth.login.return_value = (
            MagicMock(id="user-1"),
            MagicMock(access_token="token", refresh_token="refresh",
                      token_type="bearer", expires_in=3600),
        )
        mock_auth.to_user_info.return_value = MagicMock(
            id="user-1", email="test@test.com", username="test",
            full_name="", role=MagicMock(value="user"),
            is_active=True, is_verified=True,
            created_at=datetime.now(timezone.utc),
        )
        response = client.post("/auth/login", json={
            "email": "test@test.com",
            "password": "password123",
        })
        assert response.status_code == 200

    @patch("app.api.auth.auth_service")
    def test_login_invalid_credentials(self, mock_auth: MagicMock, client: TestClient):
        mock_auth.login.side_effect = ValueError("Invalid email or password")
        response = client.post("/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpass",
        })
        assert response.status_code == 401

    @patch("app.api.auth.auth_service")
    def test_refresh_token(self, mock_auth: MagicMock, client: TestClient):
        mock_auth.refresh_tokens.return_value = MagicMock(
            access_token="new-token", refresh_token="new-refresh",
            token_type="bearer", expires_in=3600,
        )
        response = client.post("/auth/refresh", json={
            "refresh_token": "old-refresh-token",
        })
        assert response.status_code == 200
