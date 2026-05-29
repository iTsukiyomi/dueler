from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ..core.database import get_db
from ..core import cache

log = logging.getLogger("dueler.repo.workspace")

COLLECTION = "workspaces"


class WorkspaceRepository:
    """
    Data-access object for teambuilder workspaces.
    """

    async def get(self, user_id: str) -> Optional[dict]:
        """
        Fetch the workspace state for a user by Discord ID.
        Checks Redis first, falls back to MongoDB.
        """
        cached = await cache.get_workspace(str(user_id))
        if cached is not None:
            return cached

        db = get_db()
        try:
            doc = await db[COLLECTION].find_one({"_id": str(user_id)})
            if doc is None:
                return None
        except Exception as e:
            log.error("Failed to read workspace from MongoDB for %s: %s", user_id, e)
            return None

        await cache.set_workspace(str(user_id), doc)
        return doc

    async def set(self, user_id: str, ws: dict) -> None:
        """
        Save the workspace state to MongoDB and cache it in Redis.
        Invalidates the old cache first to prevent race conditions.
        """
        await cache.invalidate_workspace(str(user_id))

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

        await cache.set_workspace(str(user_id), doc)

    async def delete(self, user_id: str) -> None:
        """
        Delete the workspace state from both database and cache.
        """
        await cache.invalidate_workspace(str(user_id))

        db = get_db()
        try:
            await db[COLLECTION].delete_one({"_id": str(user_id)})
        except Exception as e:
            log.error("Failed to delete workspace from MongoDB for %s: %s", user_id, e)
