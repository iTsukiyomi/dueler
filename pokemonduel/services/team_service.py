"""
pokemonduel.services.team_service
==================================
Business logic for team management — parse, validate, save, and load
party data through the :class:`TeamRepository`.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from ..core.registry import FORMS, MOVES, ABILITIES, ITEMS, NATURES
from ..repositories.team_repository import TeamRepository
from ..services.player_service import PlayerService

log = logging.getLogger("dueler.svc.team")

# Upper bound on how many teams a single user can save.
_MAX_TEAMS_PER_USER = 50

# Pokemon Showdown paste format parsing regex patterns.
_SPECIES_LINE = re.compile(
    r"^(?:(?P<nick>.+?)\s+\((?P<species>[^)]+)\)|(?P<species_only>[^\s@(]+))"
    r"(?:\s+\((?P<gender>[MF])\))?"
    r"(?:\s+@\s*(?P<item>.+))?$"
)
_STAT_LINE = re.compile(
    r"(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)", re.IGNORECASE
)

_STAT_MAP = {
    "hp": "hpev", "atk": "atkev", "def": "defev",
    "spa": "spatkev", "spd": "spdefev", "spe": "speedev",
}
_IV_MAP = {
    "hp": "hpiv", "atk": "atkiv", "def": "defiv",
    "spa": "spatkiv", "spd": "spdefiv", "spe": "speediv",
}


class TeamService:
    """
    High-level team management operations.

    Usage::

        svc = TeamService()
        team = await svc.create_from_showdown(owner_id, "my team", paste_text)
        party = await svc.load_active_party(owner_id)
    """

    def __init__(self) -> None:
        self._repo = TeamRepository()
        self._player_svc = PlayerService()

    # -- Parse Showdown format ---------------------------------------------

    def parse_showdown(self, text: str) -> list[dict]:
        """
        Parse a Pokémon Showdown team paste into the internal party format.

        Returns a list of party-slot dicts compatible with the existing
        ``pokemonduel.pokemon.create()`` function.

        Raises ``ValueError`` with a descriptive message if the paste
        is malformed or contains invalid data.
        """
        pokemon_blocks = re.split(r"\n\s*\n", text.strip())
        if not pokemon_blocks or (len(pokemon_blocks) == 1 and not pokemon_blocks[0].strip()):
            raise ValueError("Empty team paste — no Pokémon found.")

        if len(pokemon_blocks) > 6:
            raise ValueError(
                f"Team has {len(pokemon_blocks)} Pokémon — maximum is 6."
            )

        party: list[dict] = []
        for idx, block in enumerate(pokemon_blocks):
            if not block.strip():
                continue
            try:
                slot = self._parse_single_pokemon(block.strip(), idx)
            except ValueError as exc:
                raise ValueError(f"Pokémon #{idx + 1}: {exc}") from exc
            party.append(slot)

        if not party:
            raise ValueError("No valid Pokémon found in paste.")

        return party

    def _parse_single_pokemon(self, block: str, slot_idx: int) -> dict:
        """Parse a single Pokémon block from Showdown paste format."""
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            raise ValueError("Empty Pokémon block.")

        # --- Line 1: Species (nickname) @ Item ---
        first_line = lines[0]
        match = _SPECIES_LINE.match(first_line)
        if not match:
            raise ValueError(f"Could not parse species line: {first_line!r}")

        species = (match.group("species") or match.group("species_only") or "").strip()
        nickname = (match.group("nick") or "None").strip()
        item = (match.group("item") or "").strip()
        gender_raw = match.group("gender")

        species_norm = species.lower().replace(" ", "-")

        # Validate item
        item_norm = item.lower().replace(" ", "-") if item else ""
        if item_norm and item_norm not in ITEMS:
            item_norm = ""  # silently drop unknown items

        # Gender
        gender = ""
        if gender_raw == "M":
            gender = "-m"
        elif gender_raw == "F":
            gender = "-f"

        # Defaults
        slot = {
            "id": 0,
            "pokname": species,
            "poknick": nickname,
            "hpiv": 31, "atkiv": 31, "defiv": 31,
            "spatkiv": 31, "spdefiv": 31, "speediv": 31,
            "hpev": 0, "atkev": 0, "defev": 0,
            "spatkev": 0, "spdefev": 0, "speedev": 0,
            "moves": [],
            "hitem": item_norm,
            "nature": "Hardy",
            "pokelevel": 100,
            "happiness": 255,
            "ability_index": 0,
            "gender": gender,
            "shiny": False,
            "radiant": False,
            "skin": None,
        }

        # --- Remaining lines ---
        for line in lines[1:]:
            low = line.lower().strip()

            if low.startswith("ability:"):
                ability_name = line.split(":", 1)[1].strip()
                # We store ability_index; for now default to 0
                # The actual index resolution happens at battle time
                slot["ability_index"] = 0

            elif low.startswith("level:"):
                try:
                    level = int(line.split(":", 1)[1].strip())
                    slot["pokelevel"] = max(1, min(100, level))
                except ValueError:
                    pass

            elif low.startswith("shiny:"):
                slot["shiny"] = "yes" in low

            elif low.endswith("nature"):
                nature_name = line.replace("Nature", "").replace("nature", "").strip()
                if nature_name.lower() in NATURES:
                    slot["nature"] = nature_name.capitalize()

            elif low.startswith("evs:"):
                ev_str = line.split(":", 1)[1].strip()
                total = 0
                for m in _STAT_LINE.finditer(ev_str):
                    val = int(m.group(1))
                    stat = m.group(2).lower()
                    key = _STAT_MAP.get(stat)
                    if key and 0 <= val <= 252:
                        slot[key] = val
                        total += val
                if total > 510:
                    raise ValueError(f"EV total {total} exceeds 510.")

            elif low.startswith("ivs:"):
                iv_str = line.split(":", 1)[1].strip()
                for m in _STAT_LINE.finditer(iv_str):
                    val = int(m.group(1))
                    stat = m.group(2).lower()
                    key = _IV_MAP.get(stat)
                    if key and 0 <= val <= 31:
                        slot[key] = val

            elif low.startswith("- "):
                move_name = line[2:].strip().lower().replace(" ", "-")
                # pyrefly: ignore [bad-argument-type]
                if len(slot["moves"]) < 4:
                    # pyrefly: ignore [missing-attribute]
                    slot["moves"].append(move_name)

            elif low.startswith("happiness:"):
                try:
                    slot["happiness"] = max(0, min(255, int(line.split(":", 1)[1].strip())))
                except ValueError:
                    pass

        # Pad moves to 4 if fewer provided
        # pyrefly: ignore [bad-argument-type]
        while len(slot["moves"]) < 4:
            # pyrefly: ignore [missing-attribute]
            slot["moves"].append("tackle")

        return slot

    # -- CRUD operations ---------------------------------------------------

    async def create_from_showdown(
        self, owner_id: str, name: str, paste_text: str
    ) -> dict:
        """
        Parse a Showdown paste and save it as a named team.

        Raises ``ValueError`` for parse errors and
        ``pymongo.errors.DuplicateKeyError`` if the name is taken.
        """
        # Enforce team limit
        count = await self._repo.count(str(owner_id))
        if count >= _MAX_TEAMS_PER_USER:
            raise ValueError(
                f"You've reached the maximum of {_MAX_TEAMS_PER_USER} saved teams.  "
                "Delete an old team first."
            )

        pokemon = self.parse_showdown(paste_text)
        return await self._repo.create(str(owner_id), name, pokemon)

    async def create_from_raw(
        self, owner_id: str, name: str, pokemon: list[dict]
    ) -> dict:
        """Save a pre-built party list as a named team."""
        count = await self._repo.count(str(owner_id))
        if count >= _MAX_TEAMS_PER_USER:
            raise ValueError(f"Maximum of {_MAX_TEAMS_PER_USER} teams reached.")
        return await self._repo.create(str(owner_id), name, pokemon)

    async def get_team(self, owner_id: str, name: str) -> Optional[dict]:
        """Fetch a specific team."""
        return await self._repo.get(str(owner_id), name)

    async def list_teams(self, owner_id: str) -> list[dict]:
        """List all of a user's saved teams."""
        return await self._repo.list_teams(str(owner_id))

    async def update_team(
        self, owner_id: str, name: str, pokemon: list[dict]
    ) -> bool:
        """Overwrite a team's Pokémon list."""
        return await self._repo.update(str(owner_id), name, pokemon)

    async def delete_team(self, owner_id: str, name: str) -> bool:
        """Delete a team."""
        return await self._repo.delete(str(owner_id), name)

    # -- Active party convenience ------------------------------------------

    async def load_active_party(self, owner_id: str) -> Optional[list[dict]]:
        """
        Load the player's currently active party data.

        Returns ``None`` if no active party is set or the team doesn't exist.
        """
        profile = await self._player_svc.get_profile(str(owner_id))
        if profile is None or profile.get("active_party_name") is None:
            return None

        team = await self._repo.get(str(owner_id), profile["active_party_name"])
        if team is None:
            return None
        return team.get("pokemon")

    async def set_active(self, owner_id: str, team_name: str) -> bool:
        """
        Set a team as the player's active party.

        Returns ``False`` if the team doesn't exist.
        """
        team = await self._repo.get(str(owner_id), team_name)
        if team is None:
            return False
        await self._player_svc.set_active_party(str(owner_id), team_name)
        return True

    # -- Indexes -----------------------------------------------------------

    async def ensure_indexes(self) -> None:
        """Ensure database indexes exist."""
        await self._repo.ensure_indexes()
