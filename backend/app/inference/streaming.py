"""
ArmPilot-AI — Streaming Handler
Manages streaming responses with buffering, SSE formatting, and client tracking.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncGenerator, Generator, Optional

from app.core.logger import logger


class StreamingHandler:
    """Handles streaming inference responses with buffering and client management."""

    def __init__(self, buffer_size: int = 1) -> None:
        self._buffer_size = buffer_size
        self._active_streams: dict[str, dict[str, Any]] = {}
        self._stats = {
            "total_streams": 0,
            "total_tokens_streamed": 0,
            "avg_stream_duration_ms": 0.0,
        }

    @property
    def stats(self) -> dict[str, Any]:
        return self._stats.copy()

    def create_stream(self, stream_id: Optional[str] = None) -> str:
        """Create a new stream and return its ID."""
        import uuid
        sid = stream_id or f"stream-{uuid.uuid4().hex[:8]}"
        self._active_streams[sid] = {
            "id": sid,
            "started_at": time.perf_counter(),
            "tokens": 0,
            "cancelled": False,
        }
        self._stats["total_streams"] += 1
        return sid

    def cancel_stream(self, stream_id: str) -> bool:
        """Cancel an active stream."""
        stream = self._active_streams.get(stream_id)
        if stream is None:
            return False
        stream["cancelled"] = True
        logger.info("Stream %s cancelled", stream_id)
        return True

    def close_stream(self, stream_id: str) -> Optional[dict[str, Any]]:
        """Close a stream and return its summary."""
        stream = self._active_streams.pop(stream_id, None)
        if stream is None:
            return None

        duration_ms = (time.perf_counter() - stream["started_at"]) * 1000
        tokens = stream["tokens"]

        # Update stats
        self._stats["total_tokens_streamed"] += tokens
        n = self._stats["total_streams"]
        prev_avg = self._stats["avg_stream_duration_ms"]
        self._stats["avg_stream_duration_ms"] = prev_avg + (duration_ms - prev_avg) / max(n, 1)

        return {
            "stream_id": stream_id,
            "tokens": tokens,
            "duration_ms": round(duration_ms, 2),
            "cancelled": stream["cancelled"],
        }

    def format_sse(self, chunk: dict[str, Any], stream_id: str = "") -> str:
        """Format a token chunk as a Server-Sent Event."""
        event_data = {
            "token": chunk.get("token", ""),
            "is_first": chunk.get("is_first", False),
            "is_last": chunk.get("is_last", False),
        }

        if "ttft_ms" in chunk:
            event_data["ttft_ms"] = chunk["ttft_ms"]
        if "generation_time_ms" in chunk:
            event_data["generation_time_ms"] = chunk["generation_time_ms"]
        if "tokens_per_second" in chunk:
            event_data["tokens_per_second"] = chunk["tokens_per_second"]
        if stream_id:
            event_data["stream_id"] = stream_id

        payload = json.dumps(event_data)
        return f"data: {payload}\n\n"

    def format_sse_done(self, stream_id: str = "") -> str:
        """Format the [DONE] SSE event."""
        event = {"done": True}
        if stream_id:
            event["stream_id"] = stream_id
        return f"data: {json.dumps(event)}\n\ndata: [DONE]\n\n"

    def wrap_generator(
        self,
        stream_id: str,
        generator: Generator[dict[str, Any], None, None],
    ) -> Generator[str, None, None]:
        """Wrap an inference generator into SSE-formatted strings."""
        for chunk in generator:
            stream = self._active_streams.get(stream_id)
            if stream and stream.get("cancelled"):
                break

            if stream:
                stream["tokens"] += 1

            yield self.format_sse(chunk, stream_id)

            if chunk.get("is_last"):
                yield self.format_sse_done(stream_id)
                break

    async def wrap_async_generator(
        self,
        stream_id: str,
        generator: AsyncGenerator[dict[str, Any], None],
    ) -> AsyncGenerator[str, None]:
        """Wrap an async inference generator into SSE-formatted strings."""
        async for chunk in generator:
            stream = self._active_streams.get(stream_id)
            if stream and stream.get("cancelled"):
                break

            if stream:
                stream["tokens"] += 1

            yield self.format_sse(chunk, stream_id)

            if chunk.get("is_last"):
                yield self.format_sse_done(stream_id)
                break

    def list_active(self) -> list[dict[str, Any]]:
        """List all active streams."""
        active: list[dict[str, Any]] = []
        now = time.perf_counter()
        for sid, stream in self._active_streams.items():
            duration_ms = (now - stream["started_at"]) * 1000
            active.append({
                "id": sid,
                "tokens": stream["tokens"],
                "duration_ms": round(duration_ms, 2),
            })
        return active


# Singleton
streaming_handler = StreamingHandler()
