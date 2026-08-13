"""
ArmPilot-AI — History API
"""

from __future__ import annotations

from fastapi import APIRouter

from app.database.storage import storage
from app.schemas.history import HistoryEntry, HistoryResponse

router = APIRouter()


@router.get("/api/history")
async def get_history():
    """Get combined history of benchmark and optimization runs."""
    entries: list[HistoryEntry] = []

    # Benchmarks
    for b in storage.list_benchmarks():
        config = b.get("config", {})
        latency = b.get("latency", {})
        entries.append(HistoryEntry(
            id=b.get("id", ""),
            type="benchmark",
            model=config.get("model", "unknown"),
            config_summary=f"threads={config.get('threads', '?')} batch={config.get('batch_size', '?')}",
            status=b.get("status", "unknown"),
            timestamp=b.get("timestamp", ""),
            ttft_ms=b.get("ttft_ms"),
            tokens_per_second=b.get("tokens_per_second"),
            p95_latency_ms=latency.get("p95_ms"),
            memory_mb=b.get("memory_mb"),
        ))

    # Optimizations
    for o in storage.list_optimizations():
        config = o.get("config", {})
        best = o.get("best_candidate", {})
        entries.append(HistoryEntry(
            id=o.get("id", ""),
            type="optimization",
            model=config.get("model", "unknown"),
            config_summary=f"objective={config.get('objective', '?')} candidates={len(o.get('candidates', []))}",
            status=o.get("status", "unknown"),
            timestamp=o.get("timestamp", ""),
            ttft_ms=best.get("ttft_ms") if best else None,
            tokens_per_second=best.get("tokens_per_second") if best else None,
            p95_latency_ms=best.get("p95_latency_ms") if best else None,
            memory_mb=best.get("memory_mb") if best else None,
        ))

    # Sort by timestamp descending
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    return HistoryResponse(entries=entries, total=len(entries))
