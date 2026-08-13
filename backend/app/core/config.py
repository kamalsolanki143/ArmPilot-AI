"""
ArmPilot-AI — Application Configuration
Loaded from environment variables / .env file via pydantic-settings.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the ArmPilot-AI backend."""

    # ── Server ────────────────────────────────────────────────────────────
    app_name: str = "ArmPilot-AI"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default=["*"])
    log_level: str = "INFO"

    # ── Paths ─────────────────────────────────────────────────────────────
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    models_dir: Path = Field(default=Path("models"))
    data_dir: Path = Field(default=Path("data"))
    reports_dir: Path = Field(default=Path("reports"))

    # ── Inference ─────────────────────────────────────────────────────────
    default_model: Optional[str] = None
    default_runtime: str = "llama.cpp"
    default_threads: int = 4
    default_batch_size: int = 512
    default_context_length: int = 2048
    max_tokens_default: int = 256
    gpu_layers: int = 0  # CPU-only by default for Arm64

    # ── Benchmark ─────────────────────────────────────────────────────────
    benchmark_duration_default: int = 60  # seconds
    benchmark_concurrency_default: int = 1
    benchmark_warmup_requests: int = 3
    benchmark_prompt: str = "Explain the benefits of ARM64 architecture for AI inference."

    # ── Optimization ──────────────────────────────────────────────────────
    optimization_max_candidates: int = 8
    optimization_benchmark_per_candidate: int = 5

    # ── Auth / JWT ────────────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-in-production-use-a-real-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    oauth_github_client_id: str = ""
    oauth_github_client_secret: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "ARMPILOT_",
        "extra": "ignore",
    }

    def resolve_path(self, p: Path) -> Path:
        """Resolve a relative path against base_dir."""
        if p.is_absolute():
            return p
        return self.base_dir / p


settings = Settings()
