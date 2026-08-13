"""
ArmPilot-AI — Semantic Caching
Caches inference results based on semantic similarity of prompts rather than
exact-match. Uses lightweight cosine similarity with optional sentence
embeddings when available.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Optional

from app.core.logger import logger


@dataclass
class SemanticCacheEntry:
    """A single semantic cache entry."""
    prompt: str
    prompt_embedding: Optional[list[float]]
    response: Any
    model_id: str
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    prompt_hash: str = ""

    def __post_init__(self) -> None:
        if not self.prompt_hash:
            self.prompt_hash = hashlib.sha256(self.prompt.encode()).hexdigest()[:16]

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1


class SemanticCache:
    """Caches responses by semantic similarity of prompts.

    When an exact match is not found, searches for semantically similar
    prompts using cosine similarity on embeddings. Falls back to a simple
    TF-IDF-like approach if no embedding model is available.
    """

    def __init__(
        self,
        max_entries: int = 256,
        similarity_threshold: float = 0.92,
        default_ttl: float = 1800.0,
    ) -> None:
        self._max_entries = max_entries
        self._similarity_threshold = similarity_threshold
        self._default_ttl = default_ttl
        self._entries: list[SemanticCacheEntry] = []
        self._lock = Lock()
        self._embedding_fn: Any = None

    def set_embedding_function(self, fn: Any) -> None:
        """Set a custom embedding function. Must accept a list of strings
        and return a list of list[float] embeddings."""
        self._embedding_fn = fn
        logger.info("Semantic cache embedding function set")

    def get(self, prompt: str, model_id: str) -> Optional[Any]:
        """Find a cached response for a semantically similar prompt.

        Returns the cached response if found above the similarity threshold,
        or None on miss.
        """
        with self._lock:
            # Exact match first (fast path)
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            for entry in self._entries:
                if (
                    entry.prompt_hash == prompt_hash
                    and entry.model_id == model_id
                    and self._is_fresh(entry)
                ):
                    entry.touch()
                    logger.debug("Semantic cache exact hit")
                    return entry.response

            # Semantic similarity search
            query_embedding = self._embed(prompt)
            if query_embedding is None:
                return None

            best_entry: Optional[SemanticCacheEntry] = None
            best_score = 0.0

            for entry in self._entries:
                if entry.model_id != model_id or not self._is_fresh(entry):
                    continue
                if entry.prompt_embedding is None:
                    continue

                score = self._cosine_similarity(query_embedding, entry.prompt_embedding)
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_entry is not None and best_score >= self._similarity_threshold:
                best_entry.touch()
                logger.debug(
                    "Semantic cache hit (similarity=%.3f): %.60s...",
                    best_score, prompt,
                )
                return best_entry.response

            logger.debug("Semantic cache miss: %.60s...", prompt)
            return None

    def set(
        self,
        prompt: str,
        response: Any,
        model_id: str,
        embedding: Optional[list[float]] = None,
    ) -> None:
        """Store a prompt-response pair in the semantic cache."""
        if embedding is None:
            embedding = self._embed(prompt)

        with self._lock:
            # Evict if at capacity
            if len(self._entries) >= self._max_entries:
                self._evict_lru()

            entry = SemanticCacheEntry(
                prompt=prompt,
                prompt_embedding=embedding,
                response=response,
                model_id=model_id,
            )
            self._entries.append(entry)
            logger.debug(
                "Semantic cache stored: %.60s... (model=%s)",
                prompt, model_id,
            )

    def invalidate(self, prompt: str, model_id: str) -> bool:
        """Remove entries matching the exact prompt and model."""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        with self._lock:
            before = len(self._entries)
            self._entries = [
                e for e in self._entries
                if not (e.prompt_hash == prompt_hash and e.model_id == model_id)
            ]
            removed = before - len(self._entries)
            return removed > 0

    def invalidate_model(self, model_id: str) -> int:
        """Remove all entries for a model."""
        with self._lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e.model_id != model_id]
            return before - len(self._entries)

    def clear(self) -> int:
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count

    def evict_expired(self) -> int:
        """Remove expired entries."""
        with self._lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if self._is_fresh(e)]
            return before - len(self._entries)

    @property
    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "entries": len(self._entries),
                "max_entries": self._max_entries,
                "similarity_threshold": self._similarity_threshold,
                "models": list(set(e.model_id for e in self._entries)),
            }

    # ── Internal helpers ─────────────────────────────────────────────

    def _is_fresh(self, entry: SemanticCacheEntry) -> bool:
        return (time.time() - entry.created_at) < self._default_ttl

    def _evict_lru(self) -> None:
        """Remove the least recently accessed entry. Must hold lock."""
        if not self._entries:
            return
        oldest_idx = min(range(len(self._entries)), key=lambda i: self._entries[i].last_accessed)
        self._entries.pop(oldest_idx)

    def _embed(self, text: str) -> Optional[list[float]]:
        """Compute embedding for text. Returns None if no embedding function."""
        if self._embedding_fn is None:
            return self._simple_tokenize_embedding(text)
        try:
            result = self._embedding_fn([text])
            if result and len(result) > 0:
                return result[0]
        except Exception as exc:
            logger.debug("Embedding function failed: %s", exc)
        return self._simple_tokenize_embedding(text)

    @staticmethod
    def _simple_tokenize_embedding(text: str) -> list[float]:
        """Lightweight character-n-gram frequency vector as a fallback embedding.

        Produces a 256-dimensional vector from character bigram frequencies.
        Good enough for deduplication of similar prompts; not suitable for
        cross-domain semantic search.
        """
        words = text.lower().split()
        vec = [0.0] * 256

        # Character bigrams
        for ch in text.lower():
            idx = ord(ch) % 256
            vec[idx] += 1.0

        # Word-level features
        for word in words:
            idx = hash(word) % 256
            vec[idx] += 2.0

        # Normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            # Truncate to shorter length
            n = min(len(a), len(b))
            a, b = a[:n], b[:n]

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# Singleton
semantic_cache = SemanticCache()
