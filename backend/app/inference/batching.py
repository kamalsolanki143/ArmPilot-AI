"""
ArmPilot-AI — Request Batching
Batches multiple inference requests for efficient processing.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Optional

from app.core.logger import logger
from app.schemas.inference import ChatCompletionRequest


class _BatchItem:
    """A single item in a request batch."""

    __slots__ = ("id", "request", "future", "submitted_at")

    def __init__(
        self,
        request: ChatCompletionRequest,
        future: asyncio.Future[dict[str, Any]],
    ) -> None:
        self.id = f"batch-{uuid.uuid4().hex[:8]}"
        self.request = request
        self.future = future
        self.submitted_at = time.perf_counter()


class RequestBatcher:
    """Batches inference requests for efficient grouped processing."""

    def __init__(
        self,
        max_batch_size: int = 8,
        max_wait_ms: float = 50.0,
    ) -> None:
        self._max_batch_size = max_batch_size
        self._max_wait_ms = max_wait_ms
        self._pending: list[_BatchItem] = []
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._stats = {
            "total_batches": 0,
            "total_requests": 0,
            "avg_batch_size": 0.0,
        }

    @property
    def stats(self) -> dict[str, Any]:
        return self._stats.copy()

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    async def start(self) -> None:
        """Start the batching loop."""
        if self._running:
            return
        self._running = True
        self._batch_task = asyncio.create_task(self._run_loop())
        logger.info(
            "Request batcher started (max_size=%d, max_wait=%.1fms)",
            self._max_batch_size, self._max_wait_ms,
        )

    async def stop(self) -> None:
        """Stop the batching loop and flush remaining requests."""
        self._running = False
        if self._batch_task is not None:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
            self._batch_task = None

        # Flush remaining
        async with self._batch_lock:
            if self._pending:
                await self._process_batch()

        logger.info("Request batcher stopped")

    async def submit(self, request: ChatCompletionRequest) -> dict[str, Any]:
        """Submit a request to the batch queue and wait for the result."""
        future: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()
        item = _BatchItem(request, future)

        async with self._batch_lock:
            self._pending.append(item)

        if len(self._pending) >= self._max_batch_size:
            async with self._batch_lock:
                await self._process_batch()

        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Batch request {item.id} timed out")

    async def _run_loop(self) -> None:
        """Periodically flush the batch if the wait timeout is reached."""
        while self._running:
            try:
                await asyncio.sleep(self._max_wait_ms / 1000)
            except asyncio.CancelledError:
                break

            async with self._batch_lock:
                if self._pending:
                    await self._process_batch()

    async def _process_batch(self) -> None:
        """Process all pending requests as a batch."""
        if not self._pending:
            return

        batch = self._pending[:]
        self._pending.clear()

        batch_size = len(batch)
        self._stats["total_batches"] += 1
        self._stats["total_requests"] += batch_size
        n = self._stats["total_batches"]
        prev_avg = self._stats["avg_batch_size"]
        self._stats["avg_batch_size"] = prev_avg + (batch_size - prev_avg) / n

        logger.info("Processing batch of %d requests", batch_size)

        # Process each request (in a real implementation, these would be
        # batched into a single model forward pass)
        from app.services.inference_service import inference_service

        for item in batch:
            try:
                if item.future.cancelled():
                    continue

                result = inference_service.chat_completion(item.request)
                item.future.set_result({
                    "id": item.id,
                    "text": result.choices[0].message.content if result.choices else "",
                    "prompt_tokens": result.usage.prompt_tokens,
                    "completion_tokens": result.usage.completion_tokens,
                    "total_tokens": result.usage.total_tokens,
                })
            except Exception as e:
                if not item.future.done():
                    item.future.set_exception(e)


# Singleton
request_batcher = RequestBatcher()
