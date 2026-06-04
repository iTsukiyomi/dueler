"""
ai/state_adapter.py — Converts dueler's internal ``Battle`` / ``Trainer`` /
``DuelPokemon`` objects into the ``PokeEngineState`` (and friends) that
``poke_engine.monte_carlo_tree_search`` consumes.

Design constraints
──────────────────
* This module must import cleanly even if ``poke_engine`` is not installed —
  all poke_engine imports are deferred to function bodies so that the heuristic
  path keeps working without the Rust library.
* Every conversion is wrapped in try/except with sensible defaults so a single
  malformed pokemon never crashes the entire battle.
* Name normalisation follows foul-play's convention: lowercase, strip hyphens /
  spaces / apostrophes / dots.

Returned alongside the PokeEngineState is a ``bench_map`` — a dict that maps
the poke_engine bench slot index (1–5) back to the party index in
``trainer.party``, so the bridge can reverse-translate "switch:N" choices.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from .fp_constants import (
    DUELER_STATUS_TO_PE,
    DUELER_TERRAIN_TO_PE,
    DUELER_WEATHER_TO_PE,
    ELEMENT_TYPE_TO_STR,
)

if TYPE_CHECKING:
    from ..battle.battle import Battle
    from ..trainers.trainer_base import Trainer
    from ..pokemon import DuelPokemon

log = logging.getLogger("dueler.ai.state_adapter")

# ─── One-time data load ───────────────────────────────────────────────────────
_DATA = Path(__file__).parent.parent / "data"


def _normalize(name: str | None) -> str:
    """Strip everything poke_engine doesn't want and lowercase."""
    if name is None:
        return "none"
    return (
        str(name)
        .replace(" ", "")
        .replace("-", "")
        .replace(".", "")
        .replace("'", "")
        .replace("%", "")
        .replace("*", "")
        .replace(":", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
        .lower()
        .encode("ascii", "ignore")
        .decode("utf-8")
    )


def _load_json(filename: str) -> list | dict:
    path = _DATA / filename
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ability_id (int) → normalised poke_engine string  e.g. 3 → "speedboost"
_ABILITY_DATA: list[dict] = _load_json("abilities.json")
_ABILITY_ID_TO_NAME: dict[int, str] = {
    a["id"]: _normalize(a["identifier"]) for a in _ABILITY_DATA
}


# ─── Per-pokemon conversion ───────────────────────────────────────────────────

def _get_types(poke: "DuelPokemon") -> tuple[str, str]:
    """Return (type0, type1) as poke_engine strings."""
    type_ids = list(poke.type_ids)
    t0 = ELEMENT_TYPE_TO_STR.get(int(type_ids[0]), "typeless") if type_ids else "typeless"
    t1 = ELEMENT_TYPE_TO_STR.get(int(type_ids[1]), "typeless") if len(type_ids) > 1 else "typeless"
    return t0, t1


def _get_status(poke: "DuelPokemon") -> str:
    try:
        raw = poke.nv.current if poke.nv else ""
        return DUELER_STATUS_TO_PE.get(raw, "None")
    except Exception:
        return "None"


def _get_ability_name(poke: "DuelPokemon") -> str:
    try:
        ability_id = int(poke.ability_id)
        return _ABILITY_ID_TO_NAME.get(ability_id, "noability")
    except Exception:
        return "noability"


def _get_item_name(poke: "DuelPokemon") -> str:
    try:
        item = poke.held_item.get()  # returns identifier string or None
        if item is None:
            return "None"
        return _normalize(item)
    except Exception:
        return "None"


def _get_move_name(move) -> str:
    try:
        return _normalize(move.name)
    except Exception:
        return "none"


def _is_disabled(move, poke: "DuelPokemon") -> bool:
    """True if the move cannot legally be used this turn."""
    try:
        if move.pp <= 0:
            return True
        if poke.disable.active() and move is poke.disable.item:
            return True
        return False
    except Exception:
        return False


def _get_volatile_statuses(poke: "DuelPokemon") -> set[str]:
    vs: set[str] = set()
    try:
        if poke.confusion.active():
            vs.add("confusion")
        if poke.leech_seed:
            vs.add("leechseed")
        if poke.substitute > 0:
            vs.add("substitute")
        if poke.taunt.active():
            vs.add("taunt")
        if poke.locked_move is not None:
            vs.add("lockedmove")
        if poke.yawn.active():
            vs.add("yawn")
        if poke.bind.active():
            vs.add("partiallytrapped")
        if poke.encore.active():
            vs.add("encore")
    except Exception:
        pass
    return vs


def _get_volatile_durations(poke: "DuelPokemon"):
    """Return a PokeEngineVolatileStatusDurations for the active pokemon."""
    from poke_engine import VolatileStatusDurations as PEVSD

    def _turns(effect) -> int:
        try:
            return int(effect._remaining_turns or 0)
        except Exception:
            return 0

    return PEVSD(
        confusion=_turns(poke.confusion),
        lockedmove=1 if poke.locked_move is not None else 0,
        encore=_turns(poke.encore),
        slowstart=0,  # dueler doesn't track slow start turns separately
        taunt=_turns(poke.taunt),
        yawn=_turns(poke.yawn),
    )


def _substitute_hp(poke: "DuelPokemon") -> int:
    try:
        return int(poke.substitute or 0)
    except Exception:
        return 0


def _poke_to_pe(poke: "DuelPokemon"):
    """Convert a DuelPokemon to a PokeEnginePokemon."""
    from poke_engine import Pokemon as PEP, Move as PEM

    # ── Moves (always exactly 4 slots) ───────────────────────────────────────
    move_objs = list(poke.moves)[:4]
    pe_moves = [
        PEM(
            id=_get_move_name(m),
            disabled=_is_disabled(m, poke),
            pp=max(0, int(m.pp)),
        )
        for m in move_objs
    ]
    while len(pe_moves) < 4:
        pe_moves.append(PEM(id="none", disabled=True, pp=0))

    # ── Types ────────────────────────────────────────────────────────────────
    t0, t1 = _get_types(poke)

    # ── Stats ────────────────────────────────────────────────────────────────
    try:
        atk  = poke.get_raw_attack()
        def_ = poke.get_raw_defense()
        spa  = poke.get_raw_spatk()
        spd  = poke.get_raw_spdef()
        spe  = poke.get_raw_speed()
    except Exception:
        atk = def_ = spa = spd = spe = 100

    # ── HP ───────────────────────────────────────────────────────────────────
    current_hp = max(0, int(poke.hp))
    max_hp     = max(1, int(poke.starting_hp))

    # ── Sleep / rest turns ───────────────────────────────────────────────────
    try:
        sleep_turns = int(poke.nv.sleep_timer._remaining_turns or 0)
    except Exception:
        sleep_turns = 0

    # ── Weight ───────────────────────────────────────────────────────────────
    try:
        weight_kg = max(0.1, poke.starting_weight / 10.0)
    except Exception:
        weight_kg = 50.0

    # ── EVs & nature ─────────────────────────────────────────────────────────
    try:
        evs = (
            int(poke.hpev),
            int(poke.atkev),
            int(poke.defev),
            int(poke.spatkev),
            int(poke.spdefev),
            int(poke.speedev),
        )
    except Exception:
        evs = (0, 0, 0, 0, 0, 0)

    nature = _normalize(getattr(poke, "nature", "serious")) or "serious"
    species = _normalize(getattr(poke, "_name", "missingno"))

    pe_poke = PEP(
        id=species,
        level=int(poke.level),
        types=(t0, t1),
        base_types=(t0, t1),  # forms may change types; keep symmetric
        hp=current_hp,
        maxhp=max_hp,
        ability=_get_ability_name(poke),
        base_ability=_get_ability_name(poke),
        item=_get_item_name(poke),
        nature=nature,
        evs=evs,
        attack=int(atk),
        defense=int(def_),
        special_attack=int(spa),
        special_defense=int(spd),
        speed=int(spe),
        status=_get_status(poke),
        rest_turns=0,
        sleep_turns=sleep_turns,
        weight_kg=weight_kg,
        moves=pe_moves,
        tera_type="typeless",
        terastallized=False,
    )
    log.debug(
        "[SA] Converted %s → hp=%d/%d  status=%s  types=(%s,%s)  ability=%s  item=%s  moves=%s",
        species, current_hp, max_hp, _get_status(poke), t0, t1,
        _get_ability_name(poke), _get_item_name(poke),
        [m.id for m in pe_moves if m.id != "none"],
    )
    return pe_poke


def _dummy_pe_poke():
    """Return a dummy fainted pokemon to pad the side to 6 slots."""
    from poke_engine import Pokemon as PEP, Move as PEM
    dummy_moves = [PEM(id="none", disabled=True, pp=0)] * 4
    return PEP(
        id="pikachu",
        level=1,
        types=("electric", "typeless"),
        base_types=("electric", "typeless"),
        hp=0,
        maxhp=1,
        ability="static",
        base_ability="static",
        item="None",
        nature="serious",
        evs=(0, 0, 0, 0, 0, 0),
        attack=50,
        defense=40,
        special_attack=50,
        special_defense=50,
        speed=90,
        status="None",
        rest_turns=0,
        sleep_turns=0,
        weight_kg=6.0,
        moves=dummy_moves,
        tera_type="typeless",
        terastallized=False,
    )


# ─── Per-side conversion ──────────────────────────────────────────────────────

def _side_conditions(trainer: "Trainer"):
    from poke_engine import SideConditions as PESC

    def _turns(eff) -> int:
        try:
            return max(0, int(eff._remaining_turns or 0))
        except Exception:
            return 0

    def _bool(val) -> int:
        try:
            return int(bool(val))
        except Exception:
            return 0

    return PESC(
        aurora_veil=_turns(trainer.aurora_veil),
        crafty_shield=0,
        healing_wish=_bool(trainer.healing_wish),
        light_screen=_turns(trainer.light_screen),
        lucky_chant=0,
        lunar_dance=_bool(trainer.lunar_dance),
        mat_block=0,
        mist=_turns(trainer.mist),
        protect=0,
        quick_guard=0,
        reflect=_turns(trainer.reflect),
        safeguard=_turns(trainer.safeguard),
        spikes=int(trainer.spikes),
        stealth_rock=_bool(trainer.stealth_rock),
        sticky_web=_bool(trainer.sticky_web),
        tailwind=_turns(trainer.tailwind),
        toxic_count=0,
        toxic_spikes=int(trainer.toxic_spikes),
        wide_guard=0,
    )


def _last_used_move_string(trainer: "Trainer", bench_pokemon: list) -> str:
    """
    Build the 'last_used_move' string that poke_engine expects:
    "move:N" or "switch:M" or "move:none".
    """
    try:
        active = trainer.current_pokemon
        if active is None:
            return "move:none"
        lm = active.last_move
        if lm is None:
            return "move:none"
        # Check if it was a switch
        if getattr(lm, "name", "").lower() in ("baton-pass", "u-turn", "volt-switch",
                                                "parting-shot", "flip-turn"):
            return "move:0"  # approximate
        # Find the move slot index
        for i, mv in enumerate(active.moves):
            if mv is lm:
                return f"move:{i}"
        return "move:0"
    except Exception:
        return "move:none"


def trainer_to_pe_side(
    trainer: "Trainer",
    force_switch: bool = False,
) -> tuple:
    """
    Convert a dueler Trainer to (PokeEngineSide, bench_map).

    bench_map: {pe_slot_index → party_index} so the bridge can reverse-map
    "switch:N" → trainer.party[party_index].
    """
    from poke_engine import Side as PES

    active = trainer.current_pokemon

    # Build ordered bench list (preserving party order, skipping active)
    bench: list[tuple[int, object]] = [
        (pi, p)
        for pi, p in enumerate(trainer.party)
        if p is not active
    ]

    # bench_map: pe slot 1..5 → party index
    bench_map: dict[int, int] = {}
    pe_pokemon = []

    # Slot 0 = active
    if active is not None:
        try:
            pe_pokemon.append(_poke_to_pe(active))
        except Exception:
            log.exception("Failed to convert active pokemon '%s'", getattr(active, "_name", "?"))
            pe_pokemon.append(_dummy_pe_poke())
    else:
        # Force switch state: no active pokemon yet
        pe_pokemon.append(_dummy_pe_poke())

    # Slots 1–5 = bench
    for slot_i, (pi, poke) in enumerate(bench[:5], start=1):
        bench_map[slot_i] = pi
        try:
            pe_pokemon.append(_poke_to_pe(poke))
        except Exception:
            log.exception("Failed to convert bench pokemon '%s'", getattr(poke, "_name", "?"))
            pe_pokemon.append(_dummy_pe_poke())

    # Pad to exactly 6 if needed
    while len(pe_pokemon) < 6:
        pe_pokemon.append(_dummy_pe_poke())

    # Volatile statuses / durations on the active pokemon
    active_vs: set[str] = set()
    vs_durations = None
    sub_hp = 0
    if active is not None:
        try:
            active_vs = _get_volatile_statuses(active)
            vs_durations = _get_volatile_durations(active)
            sub_hp = _substitute_hp(active)
        except Exception:
            log.exception("Failed to compute volatile statuses")

    if vs_durations is None:
        from poke_engine import VolatileStatusDurations as PEVSD
        vs_durations = PEVSD(
            confusion=0, lockedmove=0, encore=0,
            slowstart=0, taunt=0, yawn=0,
        )

    # Boosts on the active pokemon
    def _boost(attr: str) -> int:
        try:
            return max(-6, min(6, int(getattr(active, attr, 0))))
        except Exception:
            return 0

    # Wish
    try:
        wish_turns = int(trainer.wish._remaining_turns or 0)
        wish_hp    = int(trainer.wish.hp or 0) if trainer.wish.hp else 0
    except Exception:
        wish_turns = wish_hp = 0

    lum = _last_used_move_string(trainer, bench)

    side = PES(
        active_index="0",
        baton_passing=bool(trainer.baton_pass is not None),
        shed_tailing=False,
        pokemon=pe_pokemon,
        side_conditions=_side_conditions(trainer),
        wish=(wish_turns, wish_hp),
        future_sight=(0, "0"),   # too complex to map precisely, safe default
        force_switch=force_switch,
        force_trapped=False,
        slow_uturn_move=False,
        volatile_statuses=active_vs,
        volatile_status_durations=vs_durations,
        substitute_health=sub_hp,
        attack_boost=_boost("attack_stage"),
        defense_boost=_boost("defense_stage"),
        special_attack_boost=_boost("spatk_stage"),
        special_defense_boost=_boost("spdef_stage"),
        speed_boost=_boost("speed_stage"),
        accuracy_boost=_boost("accuracy_stage"),
        evasion_boost=_boost("evasion_stage"),
        last_used_move=lum,
        switch_out_move_second_saved_move="NONE",
    )

    return side, bench_map


# ─── Full battle state conversion ─────────────────────────────────────────────

def battle_to_pe_state(
    battle: "Battle",
    npc_trainer: "Trainer",
    human_trainer: "Trainer",
) -> tuple:
    """
    Convert the full dueler Battle into a (PokeEngineState, bench_map) pair.

    * side_one  = NPC  (our AI — always side_one so MCTS results use side_one)
    * side_two  = human player

    bench_map: {pe_slot_index → party_index} for the NPC's party only.

    Raises any exception from poke_engine if state construction fails.
    """
    from poke_engine import State as PEState

    npc_side, bench_map = trainer_to_pe_side(
        npc_trainer,
        force_switch=(npc_trainer.current_pokemon is None),
    )
    human_side, _ = trainer_to_pe_side(
        human_trainer,
        force_switch=(human_trainer.current_pokemon is None),
    )

    # Weather
    try:
        weather_str = DUELER_WEATHER_TO_PE.get(battle.weather.get(), "none")
        weather_turns = max(-1, int(battle.weather._remaining_turns or -1))
    except Exception:
        weather_str = "none"
        weather_turns = -1

    # Terrain
    try:
        terrain_str = DUELER_TERRAIN_TO_PE.get(battle.terrain.item, "none")
        terrain_turns = max(0, int(battle.terrain._remaining_turns or 0))
    except Exception:
        terrain_str = "none"
        terrain_turns = 0

    # Trick room
    try:
        trick_room = battle.trick_room.active()
        tr_turns   = max(0, int(battle.trick_room._remaining_turns or 0))
    except Exception:
        trick_room = False
        tr_turns   = 0

    state = PEState(
        side_one=npc_side,
        side_two=human_side,
        weather=weather_str,
        weather_turns_remaining=weather_turns,
        terrain=terrain_str,
        terrain_turns_remaining=terrain_turns,
        trick_room=trick_room,
        trick_room_turns_remaining=tr_turns,
        team_preview=False,
    )

    log.debug(
        "[SA] PokeEngineState built  weather=%s(%d)  terrain=%s(%d)  trick_room=%s(%d)  bench_map=%s",
        weather_str, weather_turns,
        terrain_str, terrain_turns,
        trick_room, tr_turns,
        bench_map,
    )

    return state, bench_map
