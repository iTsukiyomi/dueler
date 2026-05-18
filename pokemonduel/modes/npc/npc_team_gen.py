"""
modes/npc/npc_team_gen.py — Random-team helpers for NPC battles.

Unchanged from the original module; preserved so the rest of the codebase
keeps importing ``generate_npc_team`` / ``convert_to_raw_data`` /
``create_npc_team`` from the same path.
"""
from ..randoms.random_team_gen import (convert_team_to_raw_data,
                                       generate_random_team)


def generate_npc_team(seed: int = None):
    """Generate a random team for the NPC opponent. Uses the same
    random-team generator as ``random battles``."""
    return generate_random_team(6, seed=seed)


def convert_to_raw_data(team, team_name: str = "NPC Team"):
    """Convert a generated team to the raw-dict format expected by
    ``pokemonduel.pokemon.create``."""
    return convert_team_to_raw_data(team, team_name)


async def create_npc_team(ctx, seed: int = None):
    """Create a full NPC team of ``DuelPokemon`` objects ready for battle."""
    from ...pokemon import create
    team_data = generate_npc_team(seed)
    raw       = convert_to_raw_data(team_data, "NPC Team")
    party = []
    for d in raw:
        party.append(await create(ctx, d))
    return party


__all__ = ["generate_npc_team", "convert_to_raw_data", "create_npc_team"]
