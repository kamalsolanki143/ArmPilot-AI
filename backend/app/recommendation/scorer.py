"""
ArmPilot-AI — Recommendation Scorer
Scores and ranks recommendations by relevance and impact.
"""

from __future__ import annotations

from typing import Any

from app.core.logger import logger
from app.schemas.benchmark import BenchmarkResult
from app.schemas.recommendation import Recommendation


# Scoring weights for different categories
_CATEGORY_WEIGHTS: dict[str, float] = {
    "latency": 1.0,
    "throughput": 0.9,
    "memory": 0.8,
    "cpu": 0.7,
    "configuration": 0.5,
}

# Severity multipliers
_SEVERITY_MULTIPLIER: dict[str, float] = {
    "critical": 1.5,
    "warning": 1.0,
    "info": 0.6,
}


class RecommendationScorer:
    """Scores and ranks recommendations based on impact and relevance."""

    def score(
        self,
        recommendations: list[Recommendation],
        result: BenchmarkResult,
    ) -> list[dict[str, Any]]:
        """Score each recommendation and return sorted results."""
        scored: list[dict[str, Any]] = []

        for rec in recommendations:
            score = self._compute_score(rec, result)
            scored.append({
                "recommendation": rec,
                "score": round(score, 3),
                "priority": self._compute_priority(score),
                "impact": self._estimate_impact(rec, result),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        logger.info(
            "Scored %d recommendations — top score: %.3f",
            len(scored),
            scored[0]["score"] if scored else 0,
        )

        return scored

    def rank(
        self,
        recommendations: list[Recommendation],
        result: BenchmarkResult,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Score, rank, and return the top N recommendations."""
        scored = self.score(recommendations, result)
        return scored[:max_results]

    def _compute_score(
        self,
        rec: Recommendation,
        result: BenchmarkResult,
    ) -> float:
        """Compute a composite score for a recommendation."""
        # Base confidence score
        base_score = rec.confidence

        # Category weight
        cat_weight = _CATEGORY_WEIGHTS.get(rec.category, 0.5)

        # Severity multiplier
        sev_mult = _SEVERITY_MULTIPLIER.get(rec.severity, 0.5)

        # Hardware context boost
        hw_boost = self._hardware_relevance_boost(rec, result)

        score = base_score * cat_weight * sev_mult * hw_boost
        return min(score, 1.0)

    def _hardware_relevance_boost(
        self,
        rec: Recommendation,
        result: BenchmarkResult,
    ) -> float:
        """Boost score if recommendation is particularly relevant to the hardware."""
        hw = result.hardware or {}
        boost = 1.0

        # Boost memory recommendations on memory-constrained devices
        total_gb = hw.get("memory_total_gb", 16)
        if rec.category == "memory" and total_gb <= 8:
            boost *= 1.3

        # Boost thread recommendations on multi-core ARM
        if rec.category == "cpu" and hw.get("is_arm64"):
            boost *= 1.2

        # Boost latency recommendations for interactive use cases
        if rec.category == "latency" and result.config.concurrency == 1:
            boost *= 1.1

        return min(boost, 1.5)

    def _compute_priority(self, score: float) -> str:
        """Map a score to a human-readable priority level."""
        if score >= 0.7:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"

    def _estimate_impact(
        self,
        rec: Recommendation,
        result: BenchmarkResult,
    ) -> dict[str, Any]:
        """Estimate the expected impact of applying this recommendation."""
        impact: dict[str, Any] = {
            "category": rec.category,
            "expected_improvement": "moderate",
        }

        if rec.category == "memory" and rec.suggested_config:
            if rec.suggested_config.get("quantization") in ("INT8", "INT4"):
                impact["expected_improvement"] = "significant"
                impact["metric"] = "memory_reduction"
                impact["estimated_percent"] = "30-60%"

        if rec.category == "latency" and rec.suggested_config:
            if "threads" in rec.suggested_config:
                impact["metric"] = "latency_reduction"
                impact["estimated_percent"] = "10-30%"

        if rec.category == "throughput" and rec.suggested_config:
            if "batch_size" in rec.suggested_config:
                impact["metric"] = "throughput_increase"
                impact["estimated_percent"] = "20-50%"

        if rec.severity == "critical":
            impact["expected_improvement"] = "significant"

        return impact


# Singleton
recommendation_scorer = RecommendationScorer()
