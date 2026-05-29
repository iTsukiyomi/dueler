from __future__ import annotations

import asyncio
from typing import List, Optional, Tuple

from ..pokemon import create as _create_poke
from ..modes.randoms.random_team_gen import (
    generate_random_team,
    generate_two_teams,
    convert_team_to_raw_data,
)


def _run_async(coro):
    """Run ``coro`` inside a fresh asyncio loop without leaking it."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # We are inside a running loop already (e.g. inside the Discord event loop). Use ``asyncio.run_coroutine_threadsafe`` semantics via a private loop on this thread instead.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


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
    # pyrefly: ignore [bad-argument-type]
    team_data = generate_random_team(team_size=team_size, seed=seed)
    raw       = convert_team_to_raw_data(team_data, "Random Team")
    return build_party(raw)


def random_two_teams(seed: Optional[int] = None) -> Tuple[List, List]:
    # pyrefly: ignore [bad-argument-type]
    t1, t2 = generate_two_teams(seed=seed)
    raw1   = convert_team_to_raw_data(t1, "Team 1")
    raw2   = convert_team_to_raw_data(t2, "Team 2")
    return build_party(raw1), build_party(raw2)


__all__ = ["build_party", "random_team", "random_two_teams"]
