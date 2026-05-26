"""
pokemonduel.core.cache
======================
Async Redis connection manager using redis.asyncio.

Reads ``REDIS_URL`` from environment variables.  Provides a singleton
Redis client with connection pooling, automatic reconnection, and
typed helper methods for the caching patterns used throughout the bot:

- **Key-value caching** (player profiles, team data)
- **Sorted sets** (Elo leaderboard)
- **Hashes** (active battle state)
- **Lists / queues** (matchmaking FIFO)

Security: Connection strings are never hardcoded.  If ``REDIS_URL``
is not set, the bot runs in **degraded mode** with caching disabled
(all cache methods return ``None`` / no-op).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import redis.asyncio as aioredis

log = logging.getLogger("dueler.cache")

_pool: Optional[aioredis.Redis] = None
_available: bool = False


async def connect() -> Optional[aioredis.Redis]:
    """
    Establish the Redis connection and return the client handle.

    If ``REDIS_URL`` is not set, logs a warning and returns ``None``.
    The bot can still function without Redis — caching is simply
    disabled and all reads fall through to MongoDB.
    """
    global _pool, _available

    if _pool is not None:
        return _pool

    url = os.environ.get("REDIS_URL")
    if not url:
        log.warning(
            "REDIS_URL not set — running in degraded mode (no caching).  "
            "Set REDIS_URL in your .env for optimal performance."
        )
        _available = False
        return None

    _pool = aioredis.from_url(
        url,
        decode_responses=False,  # we handle encoding ourselves
        max_connections=20,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )

    # Ping to verify connectivity.
    # pyrefly: ignore [not-async]
    await _pool.ping()
    _available = True
    log.info("Redis connected — %s", url.split("@")[-1] if "@" in url else url)
    return _pool


def get_redis() -> Optional[aioredis.Redis]:
    """Return the active Redis client, or ``None`` if unavailable."""
    return _pool if _available else None


def is_available() -> bool:
    """Return ``True`` if Redis is connected and functional."""
    return _available


async def close() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool, _available
    if _pool is not None:
        await _pool.aclose()
        log.info("Redis connection closed.")
        _pool = None
        _available = False


# ─────────────────────────────────────────────────────────────────────────────
# Typed helper methods
# ─────────────────────────────────────────────────────────────────────────────

async def cache_get(key: str) -> Optional[dict]:
    """Retrieve a JSON-serialised value from Redis."""
    r = get_redis()
    if r is None:
        return None
    raw = await r.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: Any, *, ttl: int = 300) -> None:
    """Store a JSON-serialisable value in Redis with a TTL (seconds)."""
    r = get_redis()
    if r is None:
        return
    await r.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(key: str) -> None:
    """Remove a key from Redis."""
    r = get_redis()
    if r is None:
        return
    await r.delete(key)


async def cache_invalidate_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern (e.g. ``player:*``)."""
    r = get_redis()
    if r is None:
        return
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break


# -- Sorted sets (leaderboard) ---------------------------------------------

async def zset_upsert(key: str, member: str, score: float) -> None:
    """Add or update a member in a sorted set."""
    r = get_redis()
    if r is None:
        return
    await r.zadd(key, {member: score})


async def zset_top(key: str, count: int = 10) -> list[tuple[str, float]]:
    """Return the top N members by descending score."""
    r = get_redis()
    if r is None:
        return []
    results = await r.zrevrange(key, 0, count - 1, withscores=True)
    return [(m.decode() if isinstance(m, bytes) else m, s) for m, s in results]


async def zset_rank(key: str, member: str) -> Optional[int]:
    """Return the 0-based rank of a member (descending). ``None`` if absent."""
    r = get_redis()
    if r is None:
        return None
    rank = await r.zrevrank(key, member)
    return rank


async def zset_score(key: str, member: str) -> Optional[float]:
    """Return the score of a member. ``None`` if absent."""
    r = get_redis()
    if r is None:
        return None
    return await r.zscore(key, member)


async def zset_remove(key: str, member: str) -> None:
    """Remove a member from a sorted set."""
    r = get_redis()
    if r is None:
        return
    await r.zrem(key, member)


# -- Hashes (battle state) -------------------------------------------------

async def hash_set(key: str, mapping: dict, *, ttl: int = 3600) -> None:
    """Store a flat dict as a Redis hash with TTL."""
    r = get_redis()
    if r is None:
        return
    encoded = {k: json.dumps(v, default=str) if not isinstance(v, (str, bytes)) else v
               for k, v in mapping.items()}
    # pyrefly: ignore [not-async]
    await r.hset(key, mapping=encoded)
    await r.expire(key, ttl)


async def hash_get_all(key: str) -> Optional[dict]:
    """Retrieve an entire Redis hash as a dict."""
    r = get_redis()
    if r is None:
        return None
    # pyrefly: ignore [not-async]
    data = await r.hgetall(key)
    if not data:
        return None
    return {k.decode() if isinstance(k, bytes) else k:
            v.decode() if isinstance(v, bytes) else v
            for k, v in data.items()}


async def hash_delete(key: str) -> None:
    """Remove a Redis hash entirely."""
    r = get_redis()
    if r is None:
        return
    await r.delete(key)


# -- Lists / queues (matchmaking) ------------------------------------------

async def queue_push(key: str, value: str) -> None:
    """Append a value to the tail of a list (FIFO)."""
    r = get_redis()
    if r is None:
        return
    # pyrefly: ignore [not-async]
    await r.rpush(key, value)


async def queue_pop(key: str) -> Optional[str]:
    """Pop a value from the head of a list (FIFO)."""
    r = get_redis()
    if r is None:
        return None
    # pyrefly: ignore [not-async]
    val = await r.lpop(key)
    # pyrefly: ignore [bad-return]
    return val.decode() if isinstance(val, bytes) else val


async def queue_remove(key: str, value: str) -> int:
    """Remove all occurrences of a value from a list. Returns count removed."""
    r = get_redis()
    if r is None:
        return 0
    # pyrefly: ignore [not-async]
    return await r.lrem(key, 0, value)


async def queue_length(key: str) -> int:
    """Return the length of a list."""
    r = get_redis()
    if r is None:
        return 0
    # pyrefly: ignore [not-async]
    return await r.llen(key)
