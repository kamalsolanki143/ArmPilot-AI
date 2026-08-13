"""
ArmPilot-AI — Configuration Advisor
Provides optimized configuration recommendations based on benchmark analysis.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.logger import logger
from app.schemas.benchmark import BenchmarkResult
from app.schemas.recommendation import Recommendation


class ConfigurationAdvisor:
    """Provides configuration tuning advice based on benchmark results."""

    def __init__(self) -> None:
        self._hardware_profiles: dict[str, dict[str, Any]] = {
            "low_memory": {
                "max_threads": 4,
                "recommended_quant": "INT4",
                "max_context": 1024,
                "max_batch": 256,
            },
            "mid_range": {
                "max_threads": 8,
                "recommended_quant": "INT8",
                "max_context": 2048,
                "max_batch": 512,
            },
            "high_end": {
                "max_threads": 16,
                "recommended_quant": "FP16",
                "max_context": 4096,
                "max_batch": 1024,
            },
        }

    def advise(
        self,
        result: BenchmarkResult,
        objective: str = "balanced",
    ) -> dict[str, Any]:
        """Generate a complete configuration advisory for the given benchmark."""
        profile = self._detect_hardware_profile(result)
        bottleneck = self._detect_bottleneck(result)

        config = self._generate_config(result, profile, bottleneck, objective)

        explanation = self._explain_config(config, result, bottleneck, objective)

        logger.info(
            "Configuration advice for benchmark %s — profile=%s, bottleneck=%s, objective=%s",
            result.id, profile, bottleneck, objective,
        )

        return {
            "profile": profile,
            "bottleneck": bottleneck,
            "objective": objective,
            "recommended_config": config,
            "explanation": explanation,
            "quick_wins": self._quick_wins(result),
        }

    def suggest_quantization(
        self,
        result: BenchmarkResult,
    ) -> list[dict[str, Any]]:
        """Suggest quantization levels with expected trade-offs."""
        suggestions: list[dict[str, Any]] = []
        current_quant = result.config.quantization or "FP16"
        memory_mb = result.memory_mb or 0
        model_size_mb = result.model_size_mb or 0

        quant_options = [
            {
                "name": "INT4",
                "expected_memory_reduction": "60-75%",
                "expected_quality_loss": "5-10%",
                "expected_speedup": "1.3-1.8x",
                "recommended": memory_mb > 3000,
            },
            {
                "name": "INT8",
                "expected_memory_reduction": "40-50%",
                "expected_quality_loss": "1-3%",
                "expected_speedup": "1.1-1.3x",
                "recommended": memory_mb > 2000,
            },
            {
                "name": "FP16",
                "expected_memory_reduction": "baseline",
                "expected_quality_loss": "none",
                "expected_speedup": "baseline",
                "recommended": memory_mb <= 2000,
            },
        ]

        for q in quant_options:
            if q["name"] == current_quant:
                q["current"] = True
            suggestions.append(q)

        return suggestions

    def suggest_threads(
        self,
        result: BenchmarkResult,
    ) -> list[dict[str, Any]]:
        """Suggest thread counts with expected impact."""
        hw = result.hardware or {}
        physical_cores = hw.get("cpu_count_physical") or hw.get("cpu_count", 4)
        current_threads = result.config.threads
        cpu_util = result.cpu_utilization_percent or 0

        suggestions: list[dict[str, Any]] = []

        for threads in [1, 2, 4, physical_cores, physical_cores * 2]:
            if threads == current_threads:
                continue
            if threads > physical_cores * 2:
                continue

            expected_impact = self._estimate_thread_impact(
                current_threads, threads, physical_cores, cpu_util
            )
            suggestions.append({
                "threads": threads,
                "ratio_to_cores": round(threads / physical_cores, 1),
                "expected_impact": expected_impact,
                "recommended": threads == physical_cores,
            })

        return sorted(suggestions, key=lambda x: x["threads"])

    def _detect_hardware_profile(self, result: BenchmarkResult) -> str:
        """Classify the hardware into a profile."""
        hw = result.hardware or {}
        memory_gb = hw.get("memory_total_gb", 8)
        cpu_count = hw.get("cpu_count", 4)

        if memory_gb <= 6 or cpu_count <= 4:
            return "low_memory"
        if memory_gb <= 16 and cpu_count <= 8:
            return "mid_range"
        return "high_end"

    def _detect_bottleneck(self, result: BenchmarkResult) -> str:
        """Identify the primary bottleneck from the result."""
        if result.cpu_utilization_percent and result.cpu_utilization_percent > 90:
            return "cpu_bound"

        if result.memory_mb and result.memory_mb > 4000:
            return "memory_bound"

        if result.ttft_ms and result.ttft_ms > 200:
            return "latency_bound"

        if result.tokens_per_second and result.tokens_per_second < 10:
            return "throughput_bound"

        return "none"

    def _generate_config(
        self,
        result: BenchmarkResult,
        profile: str,
        bottleneck: str,
        objective: str,
    ) -> dict[str, Any]:
        """Generate an optimized configuration."""
        hw_profile = self._hardware_profiles[profile]
        config: dict[str, Any] = {}

        if bottleneck == "cpu_bound":
            config["threads"] = max(1, result.config.threads - 2)
            config["concurrency"] = max(1, result.config.concurrency - 1)
            config["batch_size"] = max(64, result.config.batch_size // 2)

        elif bottleneck == "memory_bound":
            config["quantization"] = hw_profile["recommended_quant"]
            config["context_length"] = hw_profile["max_context"]
            config["batch_size"] = hw_profile["max_batch"]

        elif bottleneck == "latency_bound":
            config["threads"] = min(hw_profile["max_threads"], result.config.threads + 2)
            config["concurrency"] = 1
            if objective == "latency":
                config["quantization"] = "INT4"

        elif bottleneck == "throughput_bound":
            config["batch_size"] = min(hw_profile["max_batch"], result.config.batch_size * 2)
            config["threads"] = hw_profile["max_threads"]
            config["concurrency"] = min(4, result.config.concurrency + 1)

        else:
            # No clear bottleneck — optimize per objective
            if objective == "throughput":
                config["batch_size"] = hw_profile["max_batch"]
                config["threads"] = hw_profile["max_threads"]
            elif objective == "latency":
                config["threads"] = min(4, hw_profile["max_threads"])
                config["concurrency"] = 1
            elif objective == "memory":
                config["quantization"] = hw_profile["recommended_quant"]
            else:
                config["threads"] = min(hw_profile["max_threads"], 8)

        return config

    def _explain_config(
        self,
        config: dict[str, Any],
        result: BenchmarkResult,
        bottleneck: str,
        objective: str,
    ) -> str:
        """Generate a human-readable explanation of the recommended config."""
        parts: list[str] = []

        if bottleneck != "none":
            parts.append(f"Detected bottleneck: {bottleneck.replace('_', ' ')}.")
        else:
            parts.append("No clear bottleneck detected.")

        if "threads" in config:
            parts.append(
                f"Thread count adjusted to {config['threads']} "
                f"(was {result.config.threads})."
            )
        if "batch_size" in config:
            parts.append(
                f"Batch size adjusted to {config['batch_size']} "
                f"(was {result.config.batch_size})."
            )
        if "quantization" in config:
            parts.append(f"Recommended quantization: {config['quantization']}.")
        if "concurrency" in config:
            parts.append(
                f"Concurrency adjusted to {config['concurrency']} "
                f"(was {result.config.concurrency})."
            )
        if "context_length" in config:
            parts.append(f"Context length set to {config['context_length']}.")

        parts.append(f"Objective: {objective}.")

        return " ".join(parts)

    def _quick_wins(self, result: BenchmarkResult) -> list[str]:
        """Identify quick configuration changes with high expected impact."""
        wins: list[str] = []
        hw = result.hardware or {}
        physical_cores = hw.get("cpu_count_physical") or hw.get("cpu_count", 4)

        if result.config.threads > physical_cores:
            wins.append(f"Reduce threads from {result.config.threads} to {physical_cores} (matches physical cores)")

        if result.cpu_utilization_percent and result.cpu_utilization_percent < 30:
            wins.append("Increase thread count or concurrency — CPU is underutilized")

        if result.memory_mb and result.memory_mb > 4000:
            wins.append("Try INT8 quantization to reduce memory usage by ~40%")

        if result.ttft_ms and result.ttft_ms > 300:
            wins.append("Reduce context length to improve time-to-first-token")

        if result.tokens_per_second and result.tokens_per_second < 10:
            wins.append("Increase batch size to improve throughput")

        return wins

    def _estimate_thread_impact(
        self,
        current: int,
        suggested: int,
        physical_cores: int,
        cpu_util: float,
    ) -> str:
        """Estimate the impact of changing thread count."""
        if suggested == physical_cores:
            return "optimal — matches physical core count"
        if suggested > physical_cores:
            return "may reduce performance due to context switching"
        if suggested < current and cpu_util < 50:
            return "minimal impact — CPU is underutilized"
        return "may reduce throughput"


# Singleton
configuration_advisor = ConfigurationAdvisor()
