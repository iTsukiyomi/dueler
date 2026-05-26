"""
pokemonduel.repositories.player_repository
===========================================
CRUD + cache-aside interface for player profile documents.

Read path:  Redis cache → MongoDB fallback → cache warm
Write path: MongoDB atomic update → cache invalidate → leaderboard sync
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ..core.database import get_db
from ..core import cache
from ..models.player import COLLECTION, PlayerSchema

log = logging.getLogger("dueler.repo.player")

# Redis key templates
_CACHE_KEY = "player:{user_id}"
_CACHE_TTL = 300  # 5 minutes
_LEADERBOARD_KEY = "leaderboard:elo"


class PlayerRepository:
    """
    Data-access object for player profiles.

    All public methods are async and handle the Redis ↔ MongoDB
    cache-aside pattern transparently.
    """

    # -- Read --------------------------------------------------------------

    async def get(self, user_id: str) -> Optional[dict]:
        """
        Fetch a player profile by Discord user ID.

        Checks Redis first; falls back to MongoDB and warms the cache
        on a miss.
        """
        cache_key = _CACHE_KEY.format(user_id=user_id)

        # 1. Try cache
        cached = await cache.cache_get(cache_key)
        if cached is not None:
            return cached

        # 2. Fallback to MongoDB
        db = get_db()
        doc = await db[COLLECTION].find_one({"_id": str(user_id)})
        if doc is None:
            return None

        # 3. Warm cache
        await cache.cache_set(cache_key, doc, ttl=_CACHE_TTL)
        return doc

    async def get_or_create(self, user_id: str, username: str) -> dict:
        """
        Fetch an existing profile or create a new one.

        Uses MongoDB's ``find_one_and_update`` with ``upsert=True``
        for atomicity — no race-condition double-inserts.
        """
        db = get_db()
        now = datetime.now(timezone.utc)
        doc = await db[COLLECTION].find_one_and_update(
            {"_id": str(user_id)},
            {
                "$setOnInsert": PlayerSchema.create(user_id, username),
                "$set": {"username": username, "updated_at": now},
            },
            upsert=True,
            return_document=True,  # return the document after modification
        )

        cache_key = _CACHE_KEY.format(user_id=user_id)
        await cache.cache_set(cache_key, doc, ttl=_CACHE_TTL)

        # Ensure leaderboard is in sync
        await cache.zset_upsert(_LEADERBOARD_KEY, str(user_id), doc.get("elo", 1000))

        return doc

    # -- Write -------------------------------------------------------------

    async def update_stats(
        self,
        user_id: str,
        *,
        wins_delta: int = 0,
        losses_delta: int = 0,
        elo_delta: int = 0,
    ) -> Optional[dict]:
        """
        Atomically increment wins, losses, and Elo.

        Returns the updated document.
        """
        db = get_db()
        now = datetime.now(timezone.utc)
        doc = await db[COLLECTION].find_one_and_update(
            {"_id": str(user_id)},
            {
                "$inc": {
                    "wins": wins_delta,
                    "losses": losses_delta,
                    "elo": elo_delta,
                },
                "$set": {"updated_at": now},
            },
            return_document=True,
        )
        if doc is None:
            return None

        # Invalidate cache + sync leaderboard
        await cache.cache_delete(_CACHE_KEY.format(user_id=user_id))
        await cache.zset_upsert(_LEADERBOARD_KEY, str(user_id), doc["elo"])
        return doc

    async def update_wallet(
        self,
        user_id: str,
        *,
        wallet_delta: int = 0,
        bank_delta: int = 0,
    ) -> Optional[dict]:
        """
        Atomically adjust wallet/bank balances.

        Includes a guard to prevent negative wallet balance via a
        conditional update (the ``$inc`` only applies if the result
        would remain >= 0).
        """
        db = get_db()
        now = datetime.now(timezone.utc)

        # Build a conditional filter to prevent negative balance
        filter_doc: dict[str, Any] = {"_id": str(user_id)}
        if wallet_delta < 0:
            filter_doc["wallet"] = {"$gte": abs(wallet_delta)}
        if bank_delta < 0:
            filter_doc["bank"] = {"$gte": abs(bank_delta)}

        doc = await db[COLLECTION].find_one_and_update(
            filter_doc,
            {
                "$inc": {"wallet": wallet_delta, "bank": bank_delta},
                "$set": {"updated_at": now},
            },
            return_document=True,
        )

        if doc is not None:
            await cache.cache_delete(_CACHE_KEY.format(user_id=user_id))
        return doc

    async def set_active_party(self, user_id: str, team_name: Optional[str]) -> None:
        """Update the player's active party name."""
        db = get_db()
        await db[COLLECTION].update_one(
            {"_id": str(user_id)},
            {"$set": {
                "active_party_name": team_name,
                "updated_at": datetime.now(timezone.utc),
            }},
        )
        await cache.cache_delete(_CACHE_KEY.format(user_id=user_id))

    # -- Leaderboard -------------------------------------------------------

    async def get_leaderboard(self, offset: int = 0, limit: int = 10) -> list[dict]:
        """
        Return top players by Elo.

        Tries Redis sorted set first; falls back to a MongoDB sort.
        """
        # Try Redis
        top = await cache.zset_top(_LEADERBOARD_KEY, count=offset + limit)
        if top and len(top) > offset:
            entries = top[offset:offset + limit]
            results = []
            for user_id, elo in entries:
                profile = await self.get(str(user_id))
                if profile:
                    results.append(profile)
            return results

        # Fallback: MongoDB sort
        db = get_db()
        cursor = db[COLLECTION].find().sort("elo", -1).skip(offset).limit(limit)
        results = []
        async for doc in cursor:
            results.append(doc)
            # Warm the leaderboard cache
            await cache.zset_upsert(
                _LEADERBOARD_KEY, str(doc["_id"]), doc["elo"]
            )
        return results

    async def get_rank(self, user_id: str) -> Optional[int]:
        """Return the 1-based rank of a player on the Elo leaderboard."""
        rank = await cache.zset_rank(_LEADERBOARD_KEY, str(user_id))
        if rank is not None:
            return rank + 1  # 0-based → 1-based
        return None

    # -- Indexes -----------------------------------------------------------

    async def ensure_indexes(self) -> None:
        """Create indexes if they don't already exist."""
        db = get_db()
        collection = db[COLLECTION]
        for spec in PlayerSchema.indexes():
            keys = spec.pop("keys")
            await collection.create_index(keys, **spec)
        log.info("Player indexes ensured.")
