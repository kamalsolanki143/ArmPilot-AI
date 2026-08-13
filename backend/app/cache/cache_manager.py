"""
ArmPilot-AI — Cache Manager
Unified cache interface with LRU eviction, TTL support, and multiple backend
strategies (in-memory dict, Redis, hybrid).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional

from app.core.config import settings
from app.core.logger import logger


class LRUCache:
    """Thread-safe LRU cache with optional TTL and size limits."""

    def __init__(self, max_size: int = 1024, default_ttl: float = 300.0) -> None:
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get a value by key. Returns None if missing or expired."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None

            value, expires_at = entry
            if expires_at and time.time() > expires_at:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value with optional TTL override."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            expires_at = time.time() + (ttl if ttl is not None else self._default_ttl)
            self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> bool:
        """Remove a key. Returns True if the key existed."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """Clear all entries. Returns count of entries removed."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": self.size(),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }

    def evict_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        now = time.time()
        removed = 0
        with self._lock:
            expired_keys = [
                k for k, (_, exp) in self._cache.items()
                if exp and now > exp
            ]
            for k in expired_keys:
                del self._cache[k]
                removed += 1
        return removed


class CacheManager:
    """Unified cache manager with LRU + optional Redis backend."""

    def __init__(
        self,
        max_size: int = 1024,
        default_ttl: float = 300.0,
        namespace: str = "default",
    ) -> None:
        self._namespace = namespace
        self._lru = LRUCache(max_size=max_size, default_ttl=default_ttl)
        self._redis_client: Optional[Any] = None
        self._default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self._namespace}:{key}" if self._namespace else key

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "namespace": self._namespace,
            "lru": self._lru.stats,
            "redis_connected": self._redis_client is not None,
        }

    def get(self, key: str) -> Optional[Any]:
        """Get a value, checking LRU first then Redis."""
        full_key = self._key(key)

        # LRU first
        value = self._lru.get(full_key)
        if value is not None:
            return value

        # Redis fallback
        if self._redis_client is not None:
            try:
                raw = self._redis_client.get(full_key)
                if raw is not None:
                    value = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
                    # Promote to LRU
                    self._lru.set(full_key, value)
                    return value
            except Exception as exc:
                logger.warning("Redis get error: %s", exc)

        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value in both LRU and Redis (if available)."""
        full_key = self._key(key)
        effective_ttl = ttl if ttl is not None else self._default_ttl

        self._lru.set(full_key, value, ttl=effective_ttl)

        if self._redis_client is not None:
            try:
                serialized = json.dumps(value, default=str)
                self._redis_client.setex(full_key, int(effective_ttl), serialized)
            except Exception as exc:
                logger.warning("Redis set error: %s", exc)

    def delete(self, key: str) -> bool:
        """Delete from both backends."""
        full_key = self._key(key)
        removed = self._lru.delete(full_key)
        if self._redis_client is not None:
            try:
                self._redis_client.delete(full_key)
            except Exception as exc:
                logger.warning("Redis delete error: %s", exc)
        return removed

    def clear(self) -> None:
        """Clear the LRU cache. Does not clear Redis namespace."""
        count = self._lru.clear()
        logger.info("Cache cleared (%s): %d entries", self._namespace, count)

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate LRU entries whose keys match a substring pattern."""
        with self._lru._lock:
            keys_to_remove = [k for k in self._lru._cache if pattern in k]
            for k in keys_to_remove:
                del self._lru._cache[k]
        return len(keys_to_remove)

    def connect_redis(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ) -> bool:
        """Attempt to connect to Redis."""
        try:
            import redis
            self._redis_client = redis.Redis(
                host=host, port=port, db=db, password=password,
                decode_responses=True, socket_timeout=5,
            )
            self._redis_client.ping()
            logger.info("Redis connected: %s:%d/%d", host, port, db)
            return True
        except ImportError:
            logger.info("redis package not installed; using LRU-only cache")
            return False
        except Exception as exc:
            logger.warning("Redis connection failed: %s", exc)
            self._redis_client = None
            return False

    def evict_expired(self) -> int:
        """Evict expired entries from the LRU cache."""
        return self._lru.evict_expired()


# ── Global caches ───────────────────────────────────────────────────────

# General-purpose cache
cache = CacheManager(max_size=2048, default_ttl=600, namespace="app")

# Short-lived cache for hot data
hot_cache = CacheManager(max_size=512, default_ttl=60, namespace="hot")

# Long-lived cache for expensive computations
cold_cache = CacheManager(max_size=256, default_ttl=3600, namespace="cold")
