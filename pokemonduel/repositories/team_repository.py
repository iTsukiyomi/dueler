"""
pokemonduel.repositories.team_repository
=========================================
CRUD interface for team / party documents.

Team names are normalised to lowercase + stripped whitespace before
any database operation, enforced by :class:`TeamSchema.create`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from ..core.database import get_db
from ..models.team import COLLECTION, TeamSchema

log = logging.getLogger("dueler.repo.team")


class TeamRepository:
    """Data-access object for team documents."""

    async def create(
        self, owner_id: str, name: str, pokemon: list[dict]
    ) -> dict:
        """
        Insert a new team.

        Raises ``pymongo.errors.DuplicateKeyError`` if a team with the
        same ``(owner_id, name)`` already exists — the compound unique
        index enforces this at the database level.
        """
        db = get_db()
        doc = TeamSchema.create(owner_id, name, pokemon)
        result = await db[COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        log.info("Team created: owner=%s name=%r (%d pokémon)",
                 owner_id, name, len(pokemon))
        return doc

    async def get(self, owner_id: str, name: str) -> Optional[dict]:
        """Fetch a single team by owner and name."""
        db = get_db()
        return await db[COLLECTION].find_one({
            "owner_id": str(owner_id),
            "name": name.strip().lower(),
        })

    async def list_teams(self, owner_id: str) -> list[dict]:
        """List all teams belonging to a user."""
        db = get_db()
        cursor = db[COLLECTION].find(
            {
                "owner_id": str(owner_id),
                "name": {"$ne": "__active__"}
            },
            {"name": 1, "pokemon": 1, "updated_at": 1},
        ).sort("name", 1)
        return [doc async for doc in cursor]

    async def update(
        self, owner_id: str, name: str, pokemon: list[dict]
    ) -> bool:
        """
        Replace the Pokémon list for an existing team.

        Returns ``True`` if a document was matched and updated.
        """
        db = get_db()
        result = await db[COLLECTION].update_one(
            {"owner_id": str(owner_id), "name": name.strip().lower()},
            {"$set": {
                "pokemon": pokemon,
                "updated_at": datetime.now(timezone.utc),
            }},
        )
        return result.modified_count > 0

    async def delete(self, owner_id: str, name: str) -> bool:
        """
        Delete a team by owner and name.

        Returns ``True`` if a document was actually deleted.
        """
        db = get_db()
        result = await db[COLLECTION].delete_one({
            "owner_id": str(owner_id),
            "name": name.strip().lower(),
        })
        if result.deleted_count > 0:
            log.info("Team deleted: owner=%s name=%r", owner_id, name)
            return True
        return False

    async def count(self, owner_id: str) -> int:
        """Return how many teams a user has saved."""
        db = get_db()
        return await db[COLLECTION].count_documents(
            {
                "owner_id": str(owner_id),
                "name": {"$ne": "__active__"}
            }
        )

    # -- Indexes -----------------------------------------------------------

    async def ensure_indexes(self) -> None:
        """Create indexes if they don't already exist."""
        db = get_db()
        collection = db[COLLECTION]
        for spec in TeamSchema.indexes():
            keys = spec.pop("keys")
            await collection.create_index(keys, **spec)
        log.info("Team indexes ensured.")
