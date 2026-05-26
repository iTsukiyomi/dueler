"""
pokemonduel.models.team
=======================
MongoDB document schema for saved teams / parties.

Each user can have multiple named teams.  The compound unique index
on ``(owner_id, name)`` prevents duplicate team names per player.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Collection name in MongoDB.
COLLECTION = "teams"


class TeamSchema:
    """
    Schema definition and factory for team documents.

    Document shape::

        {
            "_id":        ObjectId("..."),         # auto
            "owner_id":   "123456789012345678",    # Discord user ID
            "name":       "hyper offence",
            "pokemon":    [ ... ],                 # list of raw party dicts
            "created_at": ISODate("..."),
            "updated_at": ISODate("..."),
        }

    The ``pokemon`` list uses the exact same structure as the legacy
    ``member_*.json`` party format, ensuring backwards compatibility
    with the existing ``create()`` function in ``pokemonduel.pokemon``.
    """

    @staticmethod
    def create(owner_id: str, name: str, pokemon: list[dict]) -> dict[str, Any]:
        """Build a new team document."""
        now = datetime.now(timezone.utc)
        return {
            "owner_id": str(owner_id),
            "name": name.strip().lower(),
            "pokemon": pokemon,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def indexes() -> list[dict]:
        """
        Return index specifications to be created on the collection.
        """
        return [
            {
                "keys": [("owner_id", 1), ("name", 1)],
                "name": "idx_owner_name_unique",
                "unique": True,
            },
            {
                "keys": [("owner_id", 1)],
                "name": "idx_owner",
            },
        ]
