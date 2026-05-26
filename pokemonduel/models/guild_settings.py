"""
pokemonduel.models.guild_settings
=================================
MongoDB document schema for per-guild configuration.

Replaces the old ``EnhancedConfigManager`` / ``GuildConfig`` file-based
system with a MongoDB-backed settings store.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Collection name in MongoDB.
COLLECTION = "guild_settings"


class GuildSettingsSchema:
    """
    Schema definition and factory for guild settings documents.

    Document shape::

        {
            "_id":          "987654321098765432",   # Guild ID
            "prefix":       ";",
            "use_threads":  false,
            "created_at":   ISODate("..."),
            "updated_at":   ISODate("..."),
        }
    """

    # Default values for new guilds.
    DEFAULTS = {
        "prefix": ";",
        "use_threads": False,
    }

    @staticmethod
    def create(guild_id: str) -> dict[str, Any]:
        """Build a new guild settings document with safe defaults."""
        now = datetime.now(timezone.utc)
        return {
            "_id": str(guild_id),
            **GuildSettingsSchema.DEFAULTS,
            "created_at": now,
            "updated_at": now,
        }
