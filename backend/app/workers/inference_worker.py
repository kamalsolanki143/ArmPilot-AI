"""
ArmPilot-AI — Inference Worker
Background worker managing model loading/unloading and inference request queue.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Optional

from app.core.logger import logger
from app.schemas.inference import ChatCompletionRequest, ChatCompletionResponse, UsageInfo
from app.services.inference_service import inference_service


class InferenceWorker:
    """Background worker that processes inference requests from a queue."""

    def __init__(self, max_queue_size: int = 100) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._active_requests: dict[str, asyncio.Future[ChatCompletionResponse]] = {}
        self._stats: dict[str, Any] = {
            "processed": 0,
            "failed": 0,
            "avg_latency_ms": 0.0,
        }

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def stats(self) -> dict[str, Any]:
        return self._stats.copy()

    async def start(self) -> None:
        """Start the background worker loop."""
        if self._running:
            logger.warning("Inference worker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Inference worker started")

    async def stop(self) -> None:
        """Stop the background worker and drain the queue."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Inference worker stopped")

    async def submit(
        self,
        request: ChatCompletionRequest,
        timeout: float = 30.0,
    ) -> ChatCompletionResponse:
        """Submit an inference request and wait for the result."""
        request_id = f"req-{uuid.uuid4().hex[:8]}"
        future: asyncio.Future[ChatCompletionResponse] = asyncio.get_event_loop().create_future()
        self._active_requests[request_id] = future

        await self._queue.put({
            "id": request_id,
            "request": request,
        })

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._active_requests.pop(request_id, None)
            raise TimeoutError(f"Inference request {request_id} timed out after {timeout}s")

    async def _run_loop(self) -> None:
        """Main worker loop that processes queued requests."""
        while self._running:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            request_id = item["id"]
            request: ChatCompletionRequest = item["request"]
            future = self._active_requests.pop(request_id, None)

            if future is None or future.cancelled():
                continue

            start = time.perf_counter()
            try:
                if request.stream:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, self._sync_stream_collect, request
                    )
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, inference_service.chat_completion, request
                    )
                self._stats["processed"] += 1
                future.set_result(result)
            except Exception as e:
                self._stats["failed"] += 1
                future.set_exception(e)

            elapsed_ms = (time.perf_counter() - start) * 1000
            self._update_avg_latency(elapsed_ms)
            self._queue.task_done()

    def _sync_stream_collect(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Collect a streaming response into a single response."""
        completion_tokens = 0
        last_content = ""

        for chunk in inference_service.chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                last_content = chunk.choices[0].delta.content
                completion_tokens += 1

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=request.model,
            choices=[],
            usage=UsageInfo(
                prompt_tokens=0,
                completion_tokens=completion_tokens,
                total_tokens=completion_tokens,
            ),
        )

    def _update_avg_latency(self, new_ms: float) -> None:
        """Update rolling average latency."""
        n = self._stats["processed"] + self._stats["failed"]
        if n <= 1:
            self._stats["avg_latency_ms"] = new_ms
        else:
            prev = self._stats["avg_latency_ms"]
            self._stats["avg_latency_ms"] = prev + (new_ms - prev) / n


# Singleton
inference_worker = InferenceWorker()
