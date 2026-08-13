"""
ArmPilot-AI — KV Cache for Inference
Manages key-value caches used during LLM inference to avoid recomputing
attention states for shared prompt prefixes.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Optional

from app.core.logger import logger


@dataclass
class KVCacheEntry:
    """A single KV cache entry."""
    prompt_hash: str
    model_id: str
    n_ctx: int
    data: Any  # Opaque tensor/buffer — runtime-specific
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1


class KVCacheManager:
    """Manages KV caches for prompt prefix reuse across inference sessions."""

    def __init__(self, max_entries: int = 16, max_size_bytes: int = 2 * 1024 * 1024 * 1024) -> None:
        self._max_entries = max_entries
        self._max_size_bytes = max_size_bytes
        self._entries: dict[str, KVCacheEntry] = {}
        self._lock = Lock()

    @staticmethod
    def compute_key(prompt: str, model_id: str, n_ctx: int) -> str:
        """Compute a deterministic cache key from prompt content and config."""
        raw = f"{model_id}:{n_ctx}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, prompt: str, model_id: str, n_ctx: int) -> Optional[KVCacheEntry]:
        """Retrieve a cached KV state for the given prompt prefix.

        Returns the entry if found and still valid, otherwise None.
        """
        key = self.compute_key(prompt, model_id, n_ctx)
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                entry.touch()
                logger.debug("KV cache hit: %s (accessed %d times)", key[:12], entry.access_count)
                return entry
            logger.debug("KV cache miss: %s", key[:12])
            return None

    def put(
        self,
        prompt: str,
        model_id: str,
        n_ctx: int,
        data: Any,
        size_bytes: int = 0,
    ) -> KVCacheEntry:
        """Store a KV cache entry. Evicts LRU entries if at capacity."""
        key = self.compute_key(prompt, model_id, n_ctx)

        with self._lock:
            # If key already exists, update it
            if key in self._entries:
                entry = self._entries[key]
                entry.data = data
                entry.size_bytes = size_bytes
                entry.touch()
                return entry

            # Evict if at capacity
            self._evict_if_needed(size_bytes)

            entry = KVCacheEntry(
                prompt_hash=key,
                model_id=model_id,
                n_ctx=n_ctx,
                data=data,
                size_bytes=size_bytes,
            )
            self._entries[key] = entry
            logger.debug(
                "KV cache stored: %s (%d bytes, model=%s)",
                key[:12], size_bytes, model_id,
            )
            return entry

    def invalidate(self, prompt: str, model_id: str, n_ctx: int) -> bool:
        """Remove a specific KV cache entry."""
        key = self.compute_key(prompt, model_id, n_ctx)
        with self._lock:
            removed = self._entries.pop(key, None)
            if removed:
                logger.debug("KV cache invalidated: %s", key[:12])
            return removed is not None

    def invalidate_model(self, model_id: str) -> int:
        """Remove all KV cache entries for a specific model."""
        with self._lock:
            keys = [k for k, v in self._entries.items() if v.model_id == model_id]
            for k in keys:
                del self._entries[k]
            if keys:
                logger.info("KV cache cleared for model %s: %d entries", model_id, len(keys))
            return len(keys)

    def clear(self) -> int:
        """Clear all KV cache entries."""
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            if count:
                logger.info("KV cache cleared: %d entries", count)
            return count

    def _evict_if_needed(self, incoming_size: int) -> None:
        """Evict LRU entries to make room. Must be called with lock held."""
        # Remove by count
        while len(self._entries) >= self._max_entries:
            oldest_key = min(self._entries, key=lambda k: self._entries[k].last_accessed)
            removed = self._entries.pop(oldest_key)
            logger.debug("KV cache evicted (count): %s", oldest_key[:12])

        # Remove by size
        total_size = sum(e.size_bytes for e in self._entries.values())
        while total_size + incoming_size > self._max_size_bytes and self._entries:
            oldest_key = min(self._entries, key=lambda k: self._entries[k].last_accessed)
            removed = self._entries.pop(oldest_key)
            total_size -= removed.size_bytes
            logger.debug("KV cache evicted (size): %s", oldest_key[:12])

    @property
    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        with self._lock:
            total_size = sum(e.size_bytes for e in self._entries.values())
            return {
                "entries": len(self._entries),
                "max_entries": self._max_entries,
                "total_size_bytes": total_size,
                "max_size_bytes": self._max_size_bytes,
                "models": list(set(e.model_id for e in self._entries.values())),
            }

    def get_prefix_match(self, prompt: str, model_id: str, n_ctx: int) -> Optional[KVCacheEntry]:
        """Find the longest cached prefix that matches the start of the prompt.

        Returns the best matching entry or None. The caller is responsible for
        determining how many tokens to skip when resuming from the cached state.
        """
        with self._lock:
            best: Optional[KVCacheEntry] = None
            best_len = 0

            for entry in self._entries.values():
                if entry.model_id != model_id or entry.n_ctx != n_ctx:
                    continue
                # Simple prefix check — in production this would compare token IDs
                if prompt.startswith(entry.prompt_hash[:16]) and len(entry.prompt_hash) > best_len:
                    best = entry
                    best_len = len(entry.prompt_hash)

            if best is not None:
                best.touch()
                logger.debug("KV cache prefix match: %s (score=%d)", best.prompt_hash[:12], best_len)

            return best


# Singleton
kv_cache = KVCacheManager()
