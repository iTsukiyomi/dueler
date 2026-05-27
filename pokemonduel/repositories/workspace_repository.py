"""
pokemonduel.repositories.workspace_repository
==============================================
CRUD + cache-aside interface for teambuilder user workspaces.

Read path:  Redis cache → MongoDB fallback → cache warm
Write path: MongoDB replacement → cache invalidate → re-cache
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ..core.database import get_db
from ..core import cache

log = logging.getLogger("dueler.repo.workspace")

COLLECTION = "workspaces"
_CACHE_KEY = "workspace:{user_id}"
_CACHE_TTL = 3600  # 1 hour


class WorkspaceRepository:
    """
    Data-access object for teambuilder workspaces.
    """

    async def get(self, user_id: str) -> Optional[dict]:
        """
        Fetch the workspace state for a user by Discord ID.
        Checks Redis first, falls back to MongoDB.
        """
        cache_key = _CACHE_KEY.format(user_id=user_id)

        # 1. Try cache
        try:
            cached = await cache.cache_get(cache_key)
            if cached is not None:
                return cached
        except Exception as e:
            log.warning("Failed to retrieve workspace cache for %s: %s", user_id, e)

        # 2. Try MongoDB
        db = get_db()
        try:
            doc = await db[COLLECTION].find_one({"_id": str(user_id)})
            if doc is None:
                return None
        except Exception as e:
            log.error("Failed to read workspace from MongoDB for %s: %s", user_id, e)
            return None

        # 3. Warm cache
        try:
            await cache.cache_set(cache_key, doc, ttl=_CACHE_TTL)
        except Exception as e:
            log.warning("Failed to set workspace cache for %s: %s", user_id, e)

        return doc

    async def set(self, user_id: str, ws: dict) -> None:
        """
        Save the workspace state to MongoDB and cache it in Redis.
        Invalidates the old cache first to prevent race conditions.
        """
        cache_key = _CACHE_KEY.format(user_id=user_id)

        # Invalidate the cache first
        try:
            await cache.cache_delete(cache_key)
        except Exception as e:
            log.warning("Failed to delete workspace cache for %s: %s", user_id, e)

        db = get_db()
        doc = {
            "_id": str(user_id),
            "team_name": ws.get("team_name"),
            "slot_idx": ws.get("slot_idx"),
            "pokemon": ws.get("pokemon"),
            "updated_at": datetime.now(timezone.utc)
        }

        try:
            await db[COLLECTION].replace_one({"_id": str(user_id)}, doc, upsert=True)
        except Exception as e:
            log.error("Failed to replace workspace in MongoDB for %s: %s", user_id, e)

        # Re-cache the newly saved document
        try:
            await cache.cache_set(cache_key, doc, ttl=_CACHE_TTL)
        except Exception as e:
            log.warning("Failed to set workspace cache for %s: %s", user_id, e)

    async def delete(self, user_id: str) -> None:
        """
        Delete the workspace state from both database and cache.
        """
        cache_key = _CACHE_KEY.format(user_id=user_id)
        try:
            await cache.cache_delete(cache_key)
        except Exception as e:
            log.warning("Failed to delete workspace cache for %s: %s", user_id, e)

        db = get_db()
        try:
            await db[COLLECTION].delete_one({"_id": str(user_id)})
        except Exception as e:
            log.error("Failed to delete workspace from MongoDB for %s: %s", user_id, e)
