"""
pokemonduel.repositories.guild_repository
==========================================
CRUD interface for per-guild settings.

Replaces the old ``EnhancedConfigManager`` / ``GuildConfig`` system
that wrote to flat JSON files on disk.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from ..core.database import get_db
from ..core import cache
from ..models.guild_settings import COLLECTION, GuildSettingsSchema

log = logging.getLogger("dueler.repo.guild")

_CACHE_KEY = "guild:{guild_id}"
_CACHE_TTL = 600  # 10 minutes


class GuildRepository:
    """Data-access object for guild settings."""

    async def get_or_create(self, guild_id: str) -> dict:
        """
        Fetch guild settings, creating defaults if the guild is new.
        """
        cache_key = _CACHE_KEY.format(guild_id=guild_id)
        cached = await cache.cache_get(cache_key)
        if cached is not None:
            return cached

        db = get_db()
        now = datetime.now(timezone.utc)
        doc = await db[COLLECTION].find_one_and_update(
            {"_id": str(guild_id)},
            {
                "$setOnInsert": GuildSettingsSchema.create(guild_id),
                "$set": {"updated_at": now},
            },
            upsert=True,
            return_document=True,
        )

        await cache.cache_set(cache_key, doc, ttl=_CACHE_TTL)
        return doc

    async def update(self, guild_id: str, **settings: Any) -> Optional[dict]:
        """
        Update one or more guild settings.

        Only keys present in ``GuildSettingsSchema.DEFAULTS`` are accepted;
        unknown keys are silently dropped to prevent injection.
        """
        allowed = GuildSettingsSchema.DEFAULTS
        safe_update = {
            k: v for k, v in settings.items() if k in allowed
        }
        if not safe_update:
            return await self.get_or_create(guild_id)

        safe_update["updated_at"] = datetime.now(timezone.utc)

        db = get_db()
        doc = await db[COLLECTION].find_one_and_update(
            {"_id": str(guild_id)},
            {"$set": safe_update},
            return_document=True,
        )

        await cache.cache_delete(_CACHE_KEY.format(guild_id=guild_id))
        return doc
