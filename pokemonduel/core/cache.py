from __future__ import annotations

from datetime import datetime, timezone
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
        decode_responses=False,
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


# Cache keys templates & TTLs (seconds)
PLAYER_PROFILE_KEY = "player:{user_id}"
PLAYER_PROFILE_TTL = 300

GUILD_SETTINGS_KEY = "guild:{guild_id}"
GUILD_SETTINGS_TTL = 600

WORKSPACE_KEY = "workspace:{user_id}"
WORKSPACE_TTL = 3600

ACTIVE_PARTY_KEY = "active_party:{user_id}"
ACTIVE_PARTY_TTL = 900

LEADERBOARD_KEY = "leaderboard:elo"

# Image Cache keys & TTLs
IMG_SETTINGS_KEY = "img:settings:{user_id}"
IMG_SETTINGS_TTL = 3600

IMG_PROFILE_KEY = "img:profile:{user_id}"
IMG_PROFILE_TTL = 3600

IMG_QI_WS_KEY = "img:qi:ws:{user_id}"
IMG_QI_WS_TTL = 3600

IMG_QI_SEARCH_KEY = "img:qi:search:{user_id}:{pokname}"
IMG_QI_SEARCH_TTL = 3600

IMG_HELP_KEY = "img:help:{user_id}:{category}:{page}"
IMG_HELP_TTL = 3600


def _prepare_datetimes(data: Any) -> Any:
    """Serialize all datetime objects in dictionaries/lists to ISO format strings."""
    if isinstance(data, dict):
        return {k: _prepare_datetimes(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_prepare_datetimes(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    return data


def _restore_datetimes(data: Any) -> Any:
    """Recursively deserialize ISO format strings back to datetime objects for known datetime keys."""
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if isinstance(k, str) and (k == "created_at" or k == "updated_at" or k.endswith("_at")) and isinstance(v, str):
                try:
                    val_str = v
                    if val_str.endswith("Z"):
                        val_str = val_str[:-1] + "+00:00"
                    new_dict[k] = datetime.fromisoformat(val_str)
                except ValueError:
                    new_dict[k] = v
            else:
                new_dict[k] = _restore_datetimes(v)
        return new_dict
    elif isinstance(data, list):
        return [_restore_datetimes(item) for item in data]
    return data


async def cache_get_bytes(key: str) -> Optional[bytes]:
    """Retrieve a raw bytes value from Redis."""
    r = get_redis()
    if r is None:
        return None
    raw = await r.get(key)
    return raw


async def cache_set_bytes(key: str, value: bytes, *, ttl: int = 3600) -> None:
    """Store a raw bytes value in Redis with a TTL (seconds)."""
    r = get_redis()
    if r is None:
        return
    await r.set(key, value, ex=ttl)


# High-level caching/invalidation helpers

async def get_player_profile(user_id: str) -> Optional[dict]:
    """Fetch cached player profile from Redis."""
    key = PLAYER_PROFILE_KEY.format(user_id=user_id)
    try:
        data = await cache_get(key)
        if data is not None:
            return _restore_datetimes(data)
    except Exception as e:
        log.warning("Failed to retrieve player profile cache for %s: %s", user_id, e)
    return None


async def set_player_profile(user_id: str, doc: dict) -> None:
    """Cache player profile in Redis and invalidate its related settings/profile/qi/help images."""
    key = PLAYER_PROFILE_KEY.format(user_id=user_id)
    try:
        await invalidate_settings_image(user_id)
        await invalidate_profile_image(user_id)
        await invalidate_qi_ws_image(user_id)
        await invalidate_all_qi_search_images(user_id)
        await invalidate_all_help_images(user_id)
        await cache_set(key, _prepare_datetimes(doc), ttl=PLAYER_PROFILE_TTL)
    except Exception as e:
        log.warning("Failed to set player profile cache for %s: %s", user_id, e)


async def invalidate_player_profile(user_id: str) -> None:
    """Remove player profile from cache and invalidate related settings/profile/qi/help images."""
    key = PLAYER_PROFILE_KEY.format(user_id=user_id)
    try:
        await cache_delete(key)
        await invalidate_settings_image(user_id)
        await invalidate_profile_image(user_id)
        await invalidate_qi_ws_image(user_id)
        await invalidate_all_qi_search_images(user_id)
        await invalidate_all_help_images(user_id)
    except Exception as e:
        log.warning("Failed to invalidate player profile cache for %s: %s", user_id, e)


async def get_guild_settings(guild_id: str) -> Optional[dict]:
    """Fetch cached guild settings from Redis."""
    key = GUILD_SETTINGS_KEY.format(guild_id=guild_id)
    try:
        data = await cache_get(key)
        if data is not None:
            return _restore_datetimes(data)
    except Exception as e:
        log.warning("Failed to retrieve guild settings cache for %s: %s", guild_id, e)
    return None


async def set_guild_settings(guild_id: str, doc: dict) -> None:
    """Cache guild settings in Redis."""
    key = GUILD_SETTINGS_KEY.format(guild_id=guild_id)
    try:
        await cache_set(key, _prepare_datetimes(doc), ttl=GUILD_SETTINGS_TTL)
    except Exception as e:
        log.warning("Failed to set guild settings cache for %s: %s", guild_id, e)


async def invalidate_guild_settings(guild_id: str) -> None:
    """Remove guild settings from Redis."""
    key = GUILD_SETTINGS_KEY.format(guild_id=guild_id)
    try:
        await cache_delete(key)
    except Exception as e:
        log.warning("Failed to delete guild settings cache for %s: %s", guild_id, e)


async def get_workspace(user_id: str) -> Optional[dict]:
    """Fetch workspace state for a user."""
    key = WORKSPACE_KEY.format(user_id=user_id)
    try:
        data = await cache_get(key)
        if data is not None:
            return _restore_datetimes(data)
    except Exception as e:
        log.warning("Failed to retrieve workspace cache for %s: %s", user_id, e)
    return None


async def set_workspace(user_id: str, doc: dict) -> None:
    """Cache workspace state in Redis and invalidate the workspace qi card image."""
    key = WORKSPACE_KEY.format(user_id=user_id)
    try:
        await invalidate_qi_ws_image(user_id)
        await cache_set(key, _prepare_datetimes(doc), ttl=WORKSPACE_TTL)
    except Exception as e:
        log.warning("Failed to set workspace cache for %s: %s", user_id, e)


async def invalidate_workspace(user_id: str) -> None:
    """Remove workspace state from Redis and invalidate workspace qi card image."""
    key = WORKSPACE_KEY.format(user_id=user_id)
    try:
        await cache_delete(key)
        await invalidate_qi_ws_image(user_id)
    except Exception as e:
        log.warning("Failed to delete workspace cache for %s: %s", user_id, e)


async def get_active_party(user_id: str) -> Optional[list[dict]]:
    """Fetch cached active party list for a user."""
    key = ACTIVE_PARTY_KEY.format(user_id=user_id)
    try:
        data = await cache_get(key)
        if data is not None:
            return _restore_datetimes(data)
    except Exception as e:
        log.warning("Failed to retrieve active party cache for %s: %s", user_id, e)
    return None


async def set_active_party(user_id: str, party: list[dict]) -> None:
    """Cache active party list in Redis and invalidate the profile trainer card image."""
    key = ACTIVE_PARTY_KEY.format(user_id=user_id)
    try:
        await invalidate_profile_image(user_id)
        await cache_set(key, _prepare_datetimes(party), ttl=ACTIVE_PARTY_TTL)
    except Exception as e:
        log.warning("Failed to set active party cache for %s: %s", user_id, e)


async def invalidate_active_party(user_id: str) -> None:
    """Remove active party list from Redis and invalidate the profile trainer card image."""
    key = ACTIVE_PARTY_KEY.format(user_id=user_id)
    try:
        await cache_delete(key)
        await invalidate_profile_image(user_id)
    except Exception as e:
        log.warning("Failed to delete active party cache for %s: %s", user_id, e)


# Leaderboard helpers

async def update_leaderboard_score(user_id: str, score: float) -> None:
    """Add or update a member score on the Elo leaderboard."""
    try:
        await zset_upsert(LEADERBOARD_KEY, str(user_id), score)
    except Exception as e:
        log.warning("Failed to update leaderboard score for %s: %s", user_id, e)


async def remove_from_leaderboard(user_id: str) -> None:
    """Remove a member from the Elo leaderboard."""
    try:
        await zset_remove(LEADERBOARD_KEY, str(user_id))
    except Exception as e:
        log.warning("Failed to remove from leaderboard score for %s: %s", user_id, e)


async def get_leaderboard_top(offset: int, limit: int) -> list[tuple[str, float]]:
    """Return top players from the leaderboard."""
    try:
        return await zset_top(LEADERBOARD_KEY, count=offset + limit)
    except Exception as e:
        log.warning("Failed to fetch top leaderboard: %s", e)
        return []


async def get_leaderboard_rank(user_id: str) -> Optional[int]:
    """Return the 1-based rank of a user on the leaderboard."""
    try:
        rank = await zset_rank(LEADERBOARD_KEY, str(user_id))
        if rank is not None:
            return rank + 1
    except Exception as e:
        log.warning("Failed to fetch rank for %s: %s", user_id, e)
    return None


# Image helpers

async def get_settings_image(user_id: str) -> Optional[bytes]:
    """Retrieve cached settings menu image bytes."""
    return await cache_get_bytes(IMG_SETTINGS_KEY.format(user_id=user_id))


async def set_settings_image(user_id: str, data: bytes) -> None:
    """Cache settings menu image bytes."""
    await cache_set_bytes(IMG_SETTINGS_KEY.format(user_id=user_id), data, ttl=IMG_SETTINGS_TTL)


async def invalidate_settings_image(user_id: str) -> None:
    """Invalidate cached settings menu image."""
    await cache_delete(IMG_SETTINGS_KEY.format(user_id=user_id))


async def get_profile_image(user_id: str) -> Optional[bytes]:
    """Retrieve cached trainer card image bytes."""
    return await cache_get_bytes(IMG_PROFILE_KEY.format(user_id=user_id))


async def set_profile_image(user_id: str, data: bytes) -> None:
    """Cache trainer card image bytes."""
    await cache_set_bytes(IMG_PROFILE_KEY.format(user_id=user_id), data, ttl=IMG_PROFILE_TTL)


async def invalidate_profile_image(user_id: str) -> None:
    """Invalidate cached trainer card image."""
    await cache_delete(IMG_PROFILE_KEY.format(user_id=user_id))


async def get_qi_ws_image(user_id: str) -> Optional[bytes]:
    """Retrieve cached workspace qi card image bytes."""
    return await cache_get_bytes(IMG_QI_WS_KEY.format(user_id=user_id))


async def set_qi_ws_image(user_id: str, data: bytes) -> None:
    """Cache workspace qi card image bytes."""
    await cache_set_bytes(IMG_QI_WS_KEY.format(user_id=user_id), data, ttl=IMG_QI_WS_TTL)


async def invalidate_qi_ws_image(user_id: str) -> None:
    """Invalidate cached workspace qi card image."""
    await cache_delete(IMG_QI_WS_KEY.format(user_id=user_id))


async def get_qi_search_image(user_id: str, pokname: str) -> Optional[bytes]:
    """Retrieve cached search qi card image bytes."""
    return await cache_get_bytes(IMG_QI_SEARCH_KEY.format(user_id=user_id, pokname=pokname.lower().strip()))


async def set_qi_search_image(user_id: str, pokname: str, data: bytes) -> None:
    """Cache search qi card image bytes."""
    await cache_set_bytes(
        IMG_QI_SEARCH_KEY.format(user_id=user_id, pokname=pokname.lower().strip()),
        data,
        ttl=IMG_QI_SEARCH_TTL
    )


async def invalidate_qi_search_image(user_id: str, pokname: str) -> None:
    """Invalidate cached search qi card image."""
    await cache_delete(IMG_QI_SEARCH_KEY.format(user_id=user_id, pokname=pokname.lower().strip()))


async def invalidate_all_qi_search_images(user_id: str) -> None:
    """Invalidate all cached search qi cards for a user."""
    pattern = f"img:qi:search:{user_id}:*"
    await cache_invalidate_pattern(pattern)


async def get_help_image(user_id: str, category: str, page: int) -> Optional[bytes]:
    """Retrieve cached help page image bytes."""
    return await cache_get_bytes(IMG_HELP_KEY.format(user_id=user_id, category=category, page=page))


async def set_help_image(user_id: str, category: str, page: int, data: bytes) -> None:
    """Cache help page image bytes."""
    await cache_set_bytes(
        IMG_HELP_KEY.format(user_id=user_id, category=category, page=page),
        data,
        ttl=IMG_HELP_TTL
    )


async def invalidate_help_image(user_id: str, category: str, page: int) -> None:
    """Invalidate a specific cached help page image."""
    await cache_delete(IMG_HELP_KEY.format(user_id=user_id, category=category, page=page))


async def invalidate_all_help_images(user_id: str) -> None:
    """Invalidate all cached help images for a user."""
    pattern = f"img:help:{user_id}:*"
    await cache_invalidate_pattern(pattern)
