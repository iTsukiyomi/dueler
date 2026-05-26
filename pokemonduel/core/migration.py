"""
pokemonduel.core.migration
============================
One-time data migration from JSON files to MongoDB.

Reads all ``data/PokemonDuel/member_*.json`` files, creates player
profiles, and saves existing parties as "legacy" teams in MongoDB.

This script is idempotent — running it multiple times will not
create duplicate records thanks to MongoDB's upsert semantics
and the compound unique index on teams.

Usage::

    python -m pokemonduel.core.migration
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

log = logging.getLogger("dueler.migration")

# Path to the legacy user data directory.
_LEGACY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "PokemonDuel"


async def migrate() -> dict:
    """
    Run the full migration and return a summary.

    Returns a dict with keys:
    - ``players_created``: number of player profiles created/updated
    - ``teams_created``: number of legacy teams saved
    - ``errors``: list of error messages
    """
    from .database import connect, close
    from ..repositories.player_repository import PlayerRepository
    from ..repositories.team_repository import TeamRepository
    from ..models.player import PlayerSchema
    from ..models.team import TeamSchema

    # Ensure environment is loaded
    load_dotenv()

    db = await connect()
    player_repo = PlayerRepository()
    team_repo = TeamRepository()

    # Ensure indexes exist
    await player_repo.ensure_indexes()
    await team_repo.ensure_indexes()

    summary = {
        "players_created": 0,
        "teams_created": 0,
        "errors": [],
    }

    if not _LEGACY_DIR.exists():
        log.warning("Legacy data directory not found: %s", _LEGACY_DIR)
        summary["errors"].append(f"Directory not found: {_LEGACY_DIR}")
        return summary

    json_files = sorted(_LEGACY_DIR.glob("member_*.json"))
    if not json_files:
        log.warning("No member_*.json files found in %s", _LEGACY_DIR)
        return summary

    log.info("Found %d legacy member files to migrate.", len(json_files))

    for filepath in json_files:
        # Extract user ID from filename: member_123456789.json → 123456789
        stem = filepath.stem  # "member_123456789"
        user_id = stem.replace("member_", "")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            msg = f"Failed to read {filepath.name}: {exc}"
            log.error(msg)
            summary["errors"].append(msg)
            continue

        party = data.get("party", [])

        # Create/update player profile
        try:
            await player_repo.get_or_create(user_id, f"Player_{user_id[:8]}")
            summary["players_created"] += 1
        except Exception as exc:
            msg = f"Player create failed for {user_id}: {exc}"
            log.error(msg)
            summary["errors"].append(msg)

        # Save party as "legacy" team
        if party:
            try:
                await team_repo.create(user_id, "legacy", party)
                summary["teams_created"] += 1
            except Exception as exc:
                # DuplicateKeyError is expected on re-runs
                if "DuplicateKeyError" in type(exc).__name__ or "duplicate key" in str(exc).lower():
                    log.debug("Team 'legacy' already exists for %s (idempotent skip).", user_id)
                else:
                    msg = f"Team create failed for {user_id}: {exc}"
                    log.error(msg)
                    summary["errors"].append(msg)

    log.info(
        "Migration complete: %d players, %d teams, %d errors.",
        summary["players_created"],
        summary["teams_created"],
        len(summary["errors"]),
    )

    await close()
    return summary


async def _main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    load_dotenv()
    result = await migrate()
    print("\n=== Migration Summary ===")
    print(f"  Players created/updated: {result['players_created']}")
    print(f"  Teams created:           {result['teams_created']}")
    if result["errors"]:
        print(f"  Errors ({len(result['errors'])}):")
        for err in result["errors"]:
            print(f"    - {err}")
    else:
        print("  Errors: 0")
    print()


if __name__ == "__main__":
    asyncio.run(_main())
