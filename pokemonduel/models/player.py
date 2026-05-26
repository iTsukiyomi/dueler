"""
pokemonduel.models.player
=========================
MongoDB document schema for player profiles.

Uses plain dicts + factory functions rather than an ORM so that the
schema is explicit, lightweight, and easy to serialise across the
Redis caching layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


# Default Elo rating for new players.
DEFAULT_ELO = 1000

# Default starting balance.
DEFAULT_WALLET = 0

# Collection name in MongoDB.
COLLECTION = "players"


class PlayerSchema:
    """
    Schema definition and factory for player documents.

    Document shape::

        {
            "_id":               "123456789012345678",   # Discord user ID
            "username":          "Ash",
            "wins":              0,
            "losses":            0,
            "elo":               1000,
            "wallet":            0,
            "active_party_name": null,
            "created_at":        ISODate("..."),
            "updated_at":        ISODate("..."),
        }
    """

    @staticmethod
    def create(user_id: str, username: str) -> dict[str, Any]:
        """Build a new player document with safe defaults."""
        now = datetime.now(timezone.utc)
        return {
            "_id": str(user_id),
            "username": username,
            "wins": 0,
            "losses": 0,
            "elo": DEFAULT_ELO,
            "wallet": DEFAULT_WALLET,
            "active_party_name": None,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def indexes() -> list[dict]:
        """
        Return index specifications to be created on the collection.

        Called once during bot startup to ensure indexes exist.
        """
        return [
            {"keys": [("elo", -1)], "name": "idx_elo_desc"},
        ]
