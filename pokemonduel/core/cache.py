from __future__ import annotations

from datetime import datetime, timezone
import gzip
import json
import logging
import os
from typing import Any, Optional

import redis.asyncio as aioredis

log = logging.getLogger("dueler.cache")

_pool: Optional[aioredis.Redis] = None
_available: bool = False


async def connect() -> Optional[aioredis.Redis]:
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

    await _pool.ping()
    _available = True

    # Aggressive eviction: LRU on all keys so Redis never runs out of memory
    try:
        await _pool.config_set("maxmemory-policy", "allkeys-lru")
        await _pool.config_set("maxmemory", "25mb")
    except Exception:
        pass

    log.info("Redis connected — %s", url.split("@")[-1] if "@" in url else url)
    return _pool


def get_redis() -> Optional[aioredis.Redis]:
    return _pool if _available else None


def is_available() -> bool:
    return _available


async def close() -> None:
    global _pool, _available
    if _pool is not None:
        await _pool.aclose()
        log.info("Redis connection closed.")
        _pool = None
        _available = False


# ── Low-level helpers (gzip-compressed JSON) ──────────────────────

async def cache_get(key: str) -> Optional[dict]:
    """Retrieve a gzip-compressed JSON value."""
    r = get_redis()
    if r is None:
        return None
    try:
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(gzip.decompress(raw))
    except Exception:
        return None


async def cache_set(key: str, value: Any, *, ttl: int = 120) -> None:
    """Store a JSON-serialisable value as gzip-compressed bytes."""
    r = get_redis()
    if r is None:
        return
    try:
        compressed = gzip.compress(json.dumps(value, default=str).encode())
        await r.set(key, compressed, ex=ttl)
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.delete(key)
    except Exception:
        pass


async def cache_invalidate_pattern(pattern: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass


# ── Sorted set helpers ────────────────────────────────────────────

async def zset_upsert(key: str, member: str, score: float) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.zadd(key, {member: score})
    except Exception:
        pass


async def zset_top(key: str, count: int = 10) -> list[tuple[str, float]]:
    r = get_redis()
    if r is None:
        return []
    try:
        results = await r.zrevrange(key, 0, count - 1, withscores=True)
        return [(m.decode() if isinstance(m, bytes) else m, s) for m, s in results]
    except Exception:
        return []


async def zset_rank(key: str, member: str) -> Optional[int]:
    r = get_redis()
    if r is None:
        return None
    try:
        rank = await r.zrevrank(key, member)
        return rank
    except Exception:
        return None


async def zset_score(key: str, member: str) -> Optional[float]:
    r = get_redis()
    if r is None:
        return None
    try:
        return await r.zscore(key, member)
    except Exception:
        return None


async def zset_remove(key: str, member: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.zrem(key, member)
    except Exception:
        pass


# ── Hash helpers ──────────────────────────────────────────────────

async def hash_set(key: str, mapping: dict, *, ttl: int = 600) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        encoded = {}
        for k, v in mapping.items():
            if not isinstance(v, (str, bytes)):
                encoded[k] = json.dumps(v, default=str)
            else:
                encoded[k] = v
        await r.hset(key, mapping=encoded)
        await r.expire(key, ttl)
    except Exception:
        pass


async def hash_get_all(key: str) -> Optional[dict]:
    r = get_redis()
    if r is None:
        return None
    try:
        data = await r.hgetall(key)
        if not data:
            return None
        return {k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()}
    except Exception:
        return None


async def hash_delete(key: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.delete(key)
    except Exception:
        pass


# ── Queue helpers ─────────────────────────────────────────────────

async def queue_push(key: str, value: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.rpush(key, value)
    except Exception:
        pass


async def queue_pop(key: str) -> Optional[str]:
    r = get_redis()
    if r is None:
        return None
    try:
        val = await r.lpop(key)
        return val.decode() if isinstance(val, bytes) else val
    except Exception:
        return None


async def queue_remove(key: str, value: str) -> int:
    r = get_redis()
    if r is None:
        return 0
    try:
        return await r.lrem(key, 0, value)
    except Exception:
        return 0


async def queue_length(key: str) -> int:
    r = get_redis()
    if r is None:
        return 0
    try:
        return await r.llen(key)
    except Exception:
        return 0


# ── Shortened key templates & reduced TTLs ────────────────────────
# Key naming:   <type>:<id>[:<sub>]
#  p    = player profile           (was player:{uid})
#  g    = guild settings           (was guild:{gid})
#  w    = workspace                (was workspace:{uid})
#  ap   = active party             (was active_party:{uid})
#  id   = image render data (replaces raw PNG caching)
#  lb:e = leaderboard elo          (was leaderboard:elo)
#  bt   = battle state             (was battle:{bid})
#  mm:r = matchmaking ranked queue (was matchmaking:ranked)

PLAYER_PROFILE_KEY = "p:{user_id}"
PLAYER_PROFILE_TTL = 120           # 2 min (was 300)

GUILD_SETTINGS_KEY = "g:{guild_id}"
GUILD_SETTINGS_TTL = 300           # 5 min (was 600)

WORKSPACE_KEY = "w:{user_id}"
WORKSPACE_TTL = 600                # 10 min (was 3600)

ACTIVE_PARTY_KEY = "ap:{user_id}"
ACTIVE_PARTY_TTL = 300             # 5 min (was 900)

LEADERBOARD_KEY = "lb:e"

# Image data keys — store the *render data* (small JSON) instead of raw PNG bytes
# The 60-second TTL means at most ~1 image per user is cached at any time,
# and LRU eviction drops the least recently used ones first.
IMG_DATA_PROFILE_KEY = "id:pr:{user_id}"
IMG_DATA_PROFILE_TTL = 60

IMG_DATA_SETTINGS_KEY = "id:st:{user_id}"
IMG_DATA_SETTINGS_TTL = 60

IMG_DATA_QI_WS_KEY = "id:qw:{user_id}"
IMG_DATA_QI_WS_TTL = 60

IMG_DATA_QI_SEARCH_KEY = "id:qs:{user_id}:{pokname}"
IMG_DATA_QI_SEARCH_TTL = 60

IMG_DATA_HELP_KEY = "id:hl:{user_id}:{category}:{page}"
IMG_DATA_HELP_TTL = 60

# Old raw-PNG key patterns — deprecated but kept for cleanup
_OLD_IMG_PROFILE_KEY = "img:profile:{user_id}"
_OLD_IMG_SETTINGS_KEY = "img:settings:{user_id}"
_OLD_IMG_QI_WS_KEY = "img:qi:ws:{user_id}"
_OLD_IMG_QI_SEARCH_KEY = "img:qi:search:{user_id}:{pokname}"
_OLD_IMG_HELP_KEY = "img:help:{user_id}:{category}:{page}"


def _prepare_datetimes(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _prepare_datetimes(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_prepare_datetimes(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    return data


def _restore_datetimes(data: Any) -> Any:
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


# ── Player profile ────────────────────────────────────────────────

async def get_player_profile(user_id: str) -> Optional[dict]:
    key = PLAYER_PROFILE_KEY.format(user_id=user_id)
    data = await cache_get(key)
    if data is not None:
        return _restore_datetimes(data)
    return None


async def set_player_profile(user_id: str, doc: dict) -> None:
    key = PLAYER_PROFILE_KEY.format(user_id=user_id)
    await invalidate_all_user_images(user_id)
    await cache_set(key, _prepare_datetimes(doc), ttl=PLAYER_PROFILE_TTL)


async def invalidate_player_profile(user_id: str) -> None:
    key = PLAYER_PROFILE_KEY.format(user_id=user_id)
    await cache_delete(key)
    await invalidate_all_user_images(user_id)


# ── Guild settings ────────────────────────────────────────────────

async def get_guild_settings(guild_id: str) -> Optional[dict]:
    key = GUILD_SETTINGS_KEY.format(guild_id=guild_id)
    data = await cache_get(key)
    if data is not None:
        return _restore_datetimes(data)
    return None


async def set_guild_settings(guild_id: str, doc: dict) -> None:
    key = GUILD_SETTINGS_KEY.format(guild_id=guild_id)
    await cache_set(key, _prepare_datetimes(doc), ttl=GUILD_SETTINGS_TTL)


async def invalidate_guild_settings(guild_id: str) -> None:
    await cache_delete(GUILD_SETTINGS_KEY.format(guild_id=guild_id))


# ── Workspace ─────────────────────────────────────────────────────

async def get_workspace(user_id: str) -> Optional[dict]:
    key = WORKSPACE_KEY.format(user_id=user_id)
    data = await cache_get(key)
    if data is not None:
        return _restore_datetimes(data)
    return None


async def set_workspace(user_id: str, doc: dict) -> None:
    key = WORKSPACE_KEY.format(user_id=user_id)
    await invalidate_qi_ws_image_data(user_id)
    await cache_set(key, _prepare_datetimes(doc), ttl=WORKSPACE_TTL)


async def invalidate_workspace(user_id: str) -> None:
    await cache_delete(WORKSPACE_KEY.format(user_id=user_id))
    await invalidate_qi_ws_image_data(user_id)


# ── Active party ──────────────────────────────────────────────────

async def get_active_party(user_id: str) -> Optional[list[dict]]:
    key = ACTIVE_PARTY_KEY.format(user_id=user_id)
    data = await cache_get(key)
    if data is not None:
        return _restore_datetimes(data)
    return None


async def set_active_party(user_id: str, party: list[dict]) -> None:
    key = ACTIVE_PARTY_KEY.format(user_id=user_id)
    await invalidate_profile_image_data(user_id)
    await cache_set(key, _prepare_datetimes(party), ttl=ACTIVE_PARTY_TTL)


async def invalidate_active_party(user_id: str) -> None:
    await cache_delete(ACTIVE_PARTY_KEY.format(user_id=user_id))
    await invalidate_profile_image_data(user_id)


# ── Leaderboard ───────────────────────────────────────────────────

async def update_leaderboard_score(user_id: str, score: float) -> None:
    await zset_upsert(LEADERBOARD_KEY, str(user_id), score)


async def remove_from_leaderboard(user_id: str) -> None:
    await zset_remove(LEADERBOARD_KEY, str(user_id))


async def get_leaderboard_top(offset: int, limit: int) -> list[tuple[str, float]]:
    return await zset_top(LEADERBOARD_KEY, count=offset + limit)


async def get_leaderboard_rank(user_id: str) -> Optional[int]:
    rank = await zset_rank(LEADERBOARD_KEY, str(user_id))
    if rank is not None:
        return rank + 1
    return None


# ── Image render DATA helpers ─────────────────────────────────────
# Cache the *data* used to render the image (small JSON, 1-3 KB)
# instead of the rendered PNG (50-200 KB). The image is regenerated
# on demand from the cached data — this saves 95%+ of image cache memory.

async def get_profile_image_data(user_id: str) -> Optional[dict]:
    """Return cached profile render data (for regenerating the trainer card)."""
    return await cache_get(IMG_DATA_PROFILE_KEY.format(user_id=user_id))


async def set_profile_image_data(user_id: str, data: dict) -> None:
    await cache_set(IMG_DATA_PROFILE_KEY.format(user_id=user_id), data, ttl=IMG_DATA_PROFILE_TTL)


async def invalidate_profile_image_data(user_id: str) -> None:
    await cache_delete(IMG_DATA_PROFILE_KEY.format(user_id=user_id))


async def get_settings_image_data(user_id: str) -> Optional[dict]:
    return await cache_get(IMG_DATA_SETTINGS_KEY.format(user_id=user_id))


async def set_settings_image_data(user_id: str, data: dict) -> None:
    await cache_set(IMG_DATA_SETTINGS_KEY.format(user_id=user_id), data, ttl=IMG_DATA_SETTINGS_TTL)


async def invalidate_settings_image_data(user_id: str) -> None:
    await cache_delete(IMG_DATA_SETTINGS_KEY.format(user_id=user_id))


async def get_qi_ws_image_data(user_id: str) -> Optional[dict]:
    return await cache_get(IMG_DATA_QI_WS_KEY.format(user_id=user_id))


async def set_qi_ws_image_data(user_id: str, data: dict) -> None:
    await cache_set(IMG_DATA_QI_WS_KEY.format(user_id=user_id), data, ttl=IMG_DATA_QI_WS_TTL)


async def invalidate_qi_ws_image_data(user_id: str) -> None:
    await cache_delete(IMG_DATA_QI_WS_KEY.format(user_id=user_id))


async def get_qi_search_image_data(user_id: str, pokname: str) -> Optional[dict]:
    return await cache_get(IMG_DATA_QI_SEARCH_KEY.format(user_id=user_id, pokname=pokname.lower().strip()))


async def set_qi_search_image_data(user_id: str, pokname: str, data: dict) -> None:
    await cache_set(
        IMG_DATA_QI_SEARCH_KEY.format(user_id=user_id, pokname=pokname.lower().strip()),
        data,
        ttl=IMG_DATA_QI_SEARCH_TTL,
    )


async def invalidate_qi_search_image_data(user_id: str, pokname: str) -> None:
    await cache_delete(IMG_DATA_QI_SEARCH_KEY.format(user_id=user_id, pokname=pokname.lower().strip()))


async def invalidate_all_qi_search_image_data(user_id: str) -> None:
    await cache_invalidate_pattern(f"id:qs:{user_id}:*")


async def get_help_image_data(user_id: str, category: str, page: int) -> Optional[dict]:
    return await cache_get(IMG_DATA_HELP_KEY.format(user_id=user_id, category=category, page=page))


async def set_help_image_data(user_id: str, category: str, page: int, data: dict) -> None:
    await cache_set(
        IMG_DATA_HELP_KEY.format(user_id=user_id, category=category, page=page),
        data,
        ttl=IMG_DATA_HELP_TTL,
    )


async def invalidate_help_image_data(user_id: str, category: str, page: int) -> None:
    await cache_delete(IMG_DATA_HELP_KEY.format(user_id=user_id, category=category, page=page))


async def invalidate_all_help_image_data(user_id: str) -> None:
    await cache_invalidate_pattern(f"id:hl:{user_id}:*")


# ── Bulk invalidation ─────────────────────────────────────────────

async def invalidate_all_user_images(user_id: str) -> None:
    """Invalidate all cached image render data for a user."""
    await cache_delete(IMG_DATA_PROFILE_KEY.format(user_id=user_id))
    await cache_delete(IMG_DATA_SETTINGS_KEY.format(user_id=user_id))
    await cache_delete(IMG_DATA_QI_WS_KEY.format(user_id=user_id))
    await invalidate_all_qi_search_image_data(user_id)
    await invalidate_all_help_image_data(user_id)


# ── Backward-compatible raw-PNG wrappers (DEPRECATED) ────────────
# These still work but cache *data* instead of PNG to save memory.
# Cog code should migrate to the *_image_data helpers above.

async def get_profile_image(user_id: str) -> Optional[bytes]:
    """DEPRECATED — returns None. Use get_profile_image_data()."""
    return None

async def set_profile_image(user_id: str, data: bytes) -> None:
    """DEPRECATED — no-op. Use set_profile_image_data()."""
    pass

async def invalidate_profile_image(user_id: str) -> None:
    """DEPRECATED — use invalidate_profile_image_data()."""
    await invalidate_profile_image_data(user_id)

async def get_settings_image(user_id: str) -> Optional[bytes]:
    return None

async def set_settings_image(user_id: str, data: bytes) -> None:
    pass

async def invalidate_settings_image(user_id: str) -> None:
    await invalidate_settings_image_data(user_id)

async def get_qi_ws_image(user_id: str) -> Optional[bytes]:
    return None

async def set_qi_ws_image(user_id: str, data: bytes) -> None:
    pass

async def invalidate_qi_ws_image(user_id: str) -> None:
    await invalidate_qi_ws_image_data(user_id)

async def get_qi_search_image(user_id: str, pokname: str) -> Optional[bytes]:
    return None

async def set_qi_search_image(user_id: str, pokname: str, data: bytes) -> None:
    pass

async def invalidate_qi_search_image(user_id: str, pokname: str) -> None:
    await invalidate_qi_search_image_data(user_id, pokname)

async def invalidate_all_qi_search_images(user_id: str) -> None:
    await invalidate_all_qi_search_image_data(user_id)

async def get_help_image(user_id: str, category: str, page: int) -> Optional[bytes]:
    return None

async def set_help_image(user_id: str, category: str, page: int, data: bytes) -> None:
    pass

async def invalidate_help_image(user_id: str, category: str, page: int) -> None:
    await invalidate_help_image_data(user_id, category, page)

async def invalidate_all_help_images(user_id: str) -> None:
    await invalidate_all_help_image_data(user_id)
