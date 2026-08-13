"""
ArmPilot-AI — Recommendation API
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse, Recommendation
from app.recommendation.engine import recommendation_engine
from app.database.storage import storage
from app.schemas.benchmark import BenchmarkResult
from app.core.exceptions import BenchmarkNotFoundError

from datetime import datetime, timezone

router = APIRouter()


@router.post("/api/recommendations")
async def generate_recommendations(request: RecommendationRequest):
    """Generate recommendations based on a benchmark result."""
    if request.benchmark_id:
        data = storage.get_benchmark(request.benchmark_id)
        if data is None:
            raise BenchmarkNotFoundError(request.benchmark_id)
        result = BenchmarkResult(**data)
        recs = recommendation_engine.analyze(result)
    else:
        # Return general recommendations if no benchmark specified
        recs = _general_recommendations()

    return RecommendationResponse(
        success=True,
        recommendations=recs,
        analyzed_benchmark_id=request.benchmark_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _general_recommendations() -> list[Recommendation]:
    """Return general getting-started recommendations."""
    import uuid
    return [
        Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity="info",
            category="configuration",
            problem="No benchmark data available",
            recommendation="Run a baseline benchmark first",
            reason="Recommendations are most effective when based on measured performance data.",
            expected_goal="Establish a performance baseline for comparison",
            confidence=1.0,
        ),
        Recommendation(
            id=f"rec-{uuid.uuid4().hex[:6]}",
            severity="info",
            category="configuration",
            problem="Default configuration active",
            recommendation="Test INT8 quantization for a good balance of speed and quality",
            reason="INT8 quantization typically provides 1.5-2x speedup with minimal quality loss.",
            expected_goal="Faster inference with acceptable quality trade-off",
            suggested_config={"quantization": "INT8"},
            confidence=0.7,
        ),
    ]
