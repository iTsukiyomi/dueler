from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ..core.database import get_db
from ..core import cache
from ..models.player import COLLECTION, PlayerSchema

log = logging.getLogger("dueler.repo.player")

class PlayerRepository:
    """
    Data-access object for player profiles.

    All public methods are async and handle the Redis ↔ MongoDB
    cache-aside pattern transparently using the core cache service.
    """

    async def get(self, user_id: str) -> Optional[dict]:
        """
        Fetch a player profile by Discord user ID.

        Checks Redis first; falls back to MongoDB and warms the cache
        on a miss.
        """
        cached = await cache.get_player_profile(str(user_id))
        if cached is not None:
            return cached

        db = get_db()
        doc = await db[COLLECTION].find_one({"_id": str(user_id)})
        if doc is None:
            return None

        await cache.set_player_profile(str(user_id), doc)
        return doc

    async def get_or_create(self, user_id: str, username: str) -> dict:
        """
        Fetch an existing profile or create a new one.

        Uses MongoDB's ``find_one_and_update`` with ``upsert=True``
        for atomicity — no race-condition double-inserts.
        """
        await cache.invalidate_player_profile(str(user_id))

        db = get_db()
        now = datetime.now(timezone.utc)

        insert_doc = PlayerSchema.create(user_id, username)
        insert_doc.pop("_id", None)
        insert_doc.pop("username", None)
        insert_doc.pop("updated_at", None)

        doc = await db[COLLECTION].find_one_and_update(
            {"_id": str(user_id)},
            {
                "$setOnInsert": insert_doc,
                "$set": {"username": username, "updated_at": now},
            },
            upsert=True,
            return_document=True,
        )

        await cache.set_player_profile(str(user_id), doc)

        if doc.get("wins", 0) > 0 or doc.get("losses", 0) > 0:
            await cache.update_leaderboard_score(str(user_id), doc.get("elo", 1000))
        else:
            await cache.remove_from_leaderboard(str(user_id))

        return doc

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
        await cache.invalidate_player_profile(str(user_id))

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

        await cache.set_player_profile(str(user_id), doc)

        if doc.get("wins", 0) > 0 or doc.get("losses", 0) > 0:
            await cache.update_leaderboard_score(str(user_id), doc["elo"])
        else:
            await cache.remove_from_leaderboard(str(user_id))
        return doc

    async def update_wallet(
        self,
        user_id: str,
        *,
        wallet_delta: int = 0,
    ) -> Optional[dict]:
        """
        Atomically adjust wallet balance.

        Includes a guard to prevent negative wallet balance via a
        conditional update (the ``$inc`` only applies if the result
        would remain >= 0).
        """
        await cache.invalidate_player_profile(str(user_id))

        db = get_db()
        now = datetime.now(timezone.utc)

        filter_doc: dict[str, Any] = {"_id": str(user_id)}
        if wallet_delta < 0:
            filter_doc["wallet"] = {"$gte": abs(wallet_delta)}

        doc = await db[COLLECTION].find_one_and_update(
            filter_doc,
            {
                "$inc": {"wallet": wallet_delta},
                "$set": {"updated_at": now},
            },
            return_document=True,
        )

        if doc is not None:
            await cache.set_player_profile(str(user_id), doc)
        return doc

    async def set_active_party(self, user_id: str, team_name: Optional[str]) -> None:
        """Update the player's active party name."""
        await cache.invalidate_player_profile(str(user_id))

        db = get_db()
        doc = await db[COLLECTION].find_one_and_update(
            {"_id": str(user_id)},
            {"$set": {
                "active_party_name": team_name,
                "updated_at": datetime.now(timezone.utc),
            }},
            return_document=True,
        )
        if doc is not None:
            await cache.set_player_profile(str(user_id), doc)

    async def get_leaderboard(self, offset: int = 0, limit: int = 10) -> list[dict]:
        """
        Return top players by Elo.

        Tries Redis sorted set first; falls back to a MongoDB sort.
        """
        top = await cache.get_leaderboard_top(offset, limit)
        if top and len(top) > offset:
            entries = top[offset:offset + limit]
            results = []
            for user_id, elo in entries:
                profile = await self.get(str(user_id))
                if profile:
                    results.append(profile)
            return results

        db = get_db()
        cursor = db[COLLECTION].find({
            "$or": [{"wins": {"$gt": 0}}, {"losses": {"$gt": 0}}]
        }).sort("elo", -1).skip(offset).limit(limit)
        results = []
        async for doc in cursor:
            results.append(doc)
            await cache.update_leaderboard_score(str(doc["_id"]), doc["elo"])
        return results

    async def get_rank(self, user_id: str) -> Optional[int]:
        """Return the 1-based rank of a player on the Elo leaderboard."""
        rank = await cache.get_leaderboard_rank(str(user_id))
        if rank is not None:
            return rank

        db = get_db()
        player = await self.get(str(user_id))
        if player is None or (player.get("wins", 0) == 0 and player.get("losses", 0) == 0):
            return None

        better_players_count = await db[COLLECTION].count_documents({
            "elo": {"$gt": player.get("elo", 1000)},
            "$or": [{"wins": {"$gt": 0}}, {"losses": {"$gt": 0}}]
        })
        return better_players_count + 1


    async def ensure_indexes(self) -> None:
        """Create indexes if they don't already exist."""
        db = get_db()
        collection = db[COLLECTION]
        for spec in PlayerSchema.indexes():
            keys = spec.pop("keys")
            await collection.create_index(keys, **spec)
        log.info("Player indexes ensured.")
