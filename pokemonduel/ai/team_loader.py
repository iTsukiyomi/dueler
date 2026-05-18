"""
ai/team_loader.py — Build real ``DuelPokemon`` parties without an event loop.

The bot's normal ``pokemon.create`` is async because the original codebase
streams data from a Mongo-ish "ctx", but in practice ``data_gen.find`` just
reads JSON from disk. That means we can drive ``create`` from a synchronous
self-play worker by spinning up a private asyncio event loop for the
duration of team creation.

We expose three helpers:

* ``build_party(raw_data_list)`` – converts a list of raw dicts (the
  ``convert_team_to_raw_data`` output) into a list of ``DuelPokemon``.
* ``random_team()`` – returns a random battle-ready party.
* ``random_two_teams()`` – two parties for an NPC-vs-NPC battle.

These run from any thread / process; the event loop is created on demand
and destroyed immediately afterwards.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional, Tuple

from ..pokemon import create as _create_poke
from ..modes.randoms.random_team_gen import (
    generate_random_team,
    generate_two_teams,
    convert_team_to_raw_data,
)


# ─────────────────────────────────────────────────────────────────────────────
def _run_async(coro):
    """Run ``coro`` inside a fresh asyncio loop without leaking it."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # We are inside a running loop already (e.g. inside the Discord
        # event loop). Use ``asyncio.run_coroutine_threadsafe`` semantics
        # via a private loop on this thread instead.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


# ─────────────────────────────────────────────────────────────────────────────
class _NullCtx:
    """Standin ``ctx`` accepted by ``data_gen.find``."""
    channel = None
    author  = None
    message = None


async def _async_build_party(raw_data_list):
    party = []
    for raw in raw_data_list:
        poke = await _create_poke(_NullCtx(), raw)
        party.append(poke)
    return party


def build_party(raw_data_list: List[dict]) -> List:
    """Synchronously build a list of ``DuelPokemon``."""
    return _run_async(_async_build_party(raw_data_list))


def random_team(seed: Optional[int] = None, team_size: int = 6) -> List:
    team_data = generate_random_team(team_size=team_size, seed=seed)
    raw       = convert_team_to_raw_data(team_data, "Random Team")
    return build_party(raw)


def random_two_teams(seed: Optional[int] = None) -> Tuple[List, List]:
    t1, t2 = generate_two_teams(seed=seed)
    raw1   = convert_team_to_raw_data(t1, "Team 1")
    raw2   = convert_team_to_raw_data(t2, "Team 2")
    return build_party(raw1), build_party(raw2)


__all__ = ["build_party", "random_team", "random_two_teams"]
