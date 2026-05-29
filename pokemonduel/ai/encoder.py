from __future__ import annotations

from typing import Optional

import numpy as np

from . import features as F
from .hidden_info import HiddenInfoTracker

try:
    from ..enums import DamageClass, ElementType, Ability  # type: ignore
except ImportError:
    DamageClass = ElementType = Ability = None   # type: ignore


def _safe(getter, default):
    try:
        v = getter()
        return default if v is None else v
    except Exception:
        return default


def _hp_ratio(p) -> float:
    if p is None:
        return 0.0
    sh = getattr(p, "starting_hp", 0) or 1
    return float(max(0, min(1, (p.hp or 0) / sh)))


def _stage(p, name) -> float:
    if p is None:
        return 0.0
    return float(getattr(p, name, 0)) / 6.0


def _expiring_active(eff) -> float:
    """Return 1.0 if an ExpiringEffect is active else 0.0."""
    if eff is None:
        return 0.0
    try:
        return 1.0 if eff.active() else 0.0
    except Exception:
        return 0.0


def _expiring_turns(eff, scale=8.0) -> float:
    if eff is None:
        return 0.0
    remain = getattr(eff, "_remaining_turns", 0) or 0
    if remain is None:
        return 1.0
    return float(min(scale, remain)) / scale


def _type_effectiveness(battle, atk_type: int, def_types: list[int]) -> float:
    """Return overall multiplier (0, .25, .5, 1, 2, 4) of an attack type vs
    a defender's type list. Falls back to 1.0 when the battle's table is empty."""
    if not battle or not getattr(battle, "type_effectiveness", None):
        return 1.0
    mult = 1.0
    te = battle.type_effectiveness
    for dt in def_types or ():
        v = te.get((int(atk_type), int(dt)))
        if v is not None:
            mult *= v / 100.0
    if battle.inverse_battle:
        # Pokémon inverse rules — convert resists/immunities to weaknesses.
        if mult == 0:
            mult = 2.0
        elif mult < 1.0:
            mult = 2.0
        elif mult > 1.0:
            mult = 0.5
    return float(mult)


def _eff_bucket(mult: float) -> int:
    """Return one-hot bucket index for an effectiveness multiplier."""
    if mult == 0:        return 0
    if mult < 0.5:       return 1
    if mult < 1.0:       return 2
    if mult < 2.0:       return 3
    if mult < 4.0:       return 4
    return 4


def _write_poke_block(buf: np.ndarray, off: int, poke, *,
                      visible: bool, opponent_active, battle,
                      hidden: Optional[HiddenInfoTracker] = None,
                      slot_idx: int = 0) -> None:
    """Fill a single Pokémon block into ``buf`` starting at ``off``.

    ``visible=False`` is used for opponent bench Pokémon that have not yet
    been revealed — most fields are zeroed and we lean on the hidden-info
    estimator to fill probabilities elsewhere in the vector.
    """
    if poke is None:
        return

    p = poke
    fainted = (getattr(p, "hp", 0) or 0) <= 0

    cur = off
    species_id = getattr(p, "pokemon_id", 0) or 0
    if visible:
        buf[cur + F.bucket(species_id, F.POKE_BLOCK.species_oh, F.N_SPECIES)] = 1.0
    cur += F.POKE_BLOCK.species_oh

    if visible:
        for t in (getattr(p, "type_ids", None) or ()):
            ti = int(t)
            if 0 <= ti < F.POKE_BLOCK.type_oh:
                buf[cur + ti] = 1.0
    cur += F.POKE_BLOCK.type_oh

    tera = getattr(p, "tera_type", None)
    if visible and tera is not None:
        try:
            ti = int(tera)
            if 0 <= ti < F.POKE_BLOCK.tera_oh:
                buf[cur + ti] = 1.0
        except Exception:
            pass
    cur += F.POKE_BLOCK.tera_oh

    if visible:
        ab = getattr(p, "ability_id", 0) or 0
        buf[cur + F.bucket(ab, F.POKE_BLOCK.ability_oh, F.N_ABILITIES)] = 1.0
    cur += F.POKE_BLOCK.ability_oh

    if visible:
        hi = getattr(p, "held_item", None)
        item_id = 0
        if hi is not None:
            item = getattr(hi, "item", None)
            item_id = getattr(item, "id", 0) or 0
        buf[cur + F.bucket(item_id, F.POKE_BLOCK.item_oh, F.N_ITEMS)] = 1.0
    cur += F.POKE_BLOCK.item_oh

    nv = getattr(p, "nv", None)
    nv_cur = (getattr(nv, "current", "") if nv is not None else "") or ""
    buf[cur + F.status_index(nv_cur)] = 1.0
    cur += F.POKE_BLOCK.status_oh

    buf[cur] = _hp_ratio(p)
    cur += F.POKE_BLOCK.hp

    if visible:
        try:
            buf[cur + 0] = min(1.0, (getattr(p, "starting_hp", 0) or 0) / 700.0)
            buf[cur + 1] = min(1.0, (getattr(p, "attack",  0) or 0) / 400.0)
            buf[cur + 2] = min(1.0, (getattr(p, "defense", 0) or 0) / 400.0)
            buf[cur + 3] = min(1.0, (getattr(p, "spatk",   0) or 0) / 400.0)
            buf[cur + 4] = min(1.0, (getattr(p, "spdef",   0) or 0) / 400.0)
            buf[cur + 5] = min(1.0, (getattr(p, "speed",   0) or 0) / 400.0)
        except Exception:
            pass
    cur += F.POKE_BLOCK.stats

    buf[cur + 0] = _stage(p, "attack_stage")
    buf[cur + 1] = _stage(p, "defense_stage")
    buf[cur + 2] = _stage(p, "spatk_stage")
    buf[cur + 3] = _stage(p, "spdef_stage")
    buf[cur + 4] = _stage(p, "speed_stage")
    buf[cur + 5] = _stage(p, "accuracy_stage")
    buf[cur + 6] = _stage(p, "evasion_stage")
    cur += F.POKE_BLOCK.stages

    flags = [
        1.0 if fainted else 0.0,
        1.0 if getattr(p, "has_mega_evolved", False) else 0.0,
        1.0 if (getattr(p, "held_item", None)
                and getattr(p.held_item, "name", None) in (
                    "mega-stone", "mega-stone-x", "mega-stone-y"))
            and not getattr(p.owner, "has_mega_evolved", False) else 0.0,
        1.0 if (getattr(p, "substitute", 0) or 0) > 0 else 0.0,
        1.0 if getattr(p, "leech_seed", False) else 0.0,
        _expiring_active(getattr(p, "confusion", None)),
        _expiring_active(getattr(p, "taunt", None)),
        _expiring_active(getattr(p, "encore", None)),
        _expiring_active(getattr(p, "disable", None)),
        _expiring_active(getattr(p, "heal_block", None)),
        _expiring_active(getattr(p, "perish_song", None)),
        _expiring_active(getattr(p, "magnet_rise", None)),
        1.0 if getattr(p, "trapping", False) else 0.0,
        1.0 if getattr(p, "ingrain", False) else 0.0,
        1.0 if getattr(p, "no_retreat", False) else 0.0,
        1.0 if getattr(p, "flash_fire", False) else 0.0,
        1.0 if getattr(p, "rage", False) else 0.0,
        1.0 if getattr(p, "destiny_bond", False) else 0.0,
        1.0 if getattr(p, "torment", False) else 0.0,
        1.0 if getattr(p, "imprison", False) else 0.0,
        1.0 if getattr(p, "ate_berry", False) else 0.0,
        1.0 if getattr(p, "stockpile", 0) else 0.0,
        1.0 if getattr(p, "focus_energy", False) else 0.0,
        1.0 if getattr(p, "yawn", None) and getattr(p.yawn, "active", lambda: False)() else 0.0,
    ]
    for i, f in enumerate(flags[:F.POKE_BLOCK.flags]):
        buf[cur + i] = f
    cur += F.POKE_BLOCK.flags

    if visible and getattr(p, "moves", None):
        move_off = cur
        opp_types = getattr(opponent_active, "type_ids", None) or [] if opponent_active else []
        own_types = getattr(p, "type_ids", None) or []
        for mi in range(F.MOVES_PER_POKE):
            base = move_off
            m = p.moves[mi] if mi < len(p.moves) else None
            if m is not None:
                ti = int(getattr(m, "type", 0)) or 0
                if 0 <= ti < F.N_TYPES:
                    buf[base + ti] = 1.0
            base += F.N_TYPES
            if m is not None:
                dc = int(getattr(m, "damage_class", 0)) or 0
                if 0 <= dc < F.N_DAMAGE_CLASS:
                    buf[base + dc] = 1.0
            base += F.N_DAMAGE_CLASS
            if m is not None:
                buf[base + 0] = min(1.0, ((m.power or 0) / 200.0))
            base += 1
            if m is not None:
                acc = m.accuracy
                buf[base + 0] = 1.0 if acc is None else min(1.0, acc / 100.0)
            base += 1
            if m is not None:
                buf[base + 0] = float(getattr(m, "priority", 0) or 0) / 7.0
            base += 1
            if m is not None:
                pp_max = max(1, getattr(m, "starting_pp", m.pp or 1))
                buf[base + 0] = min(1.0, (m.pp or 0) / pp_max)
                buf[base + 1] = min(1.0, pp_max / 64.0)
            base += 2
            if m is not None and own_types and int(getattr(m, "type", -1)) in own_types:
                buf[base + 0] = 1.0
            base += 1
            if m is not None and opp_types:
                mult = _type_effectiveness(battle, int(getattr(m, "type", 0)), opp_types)
                idx = _eff_bucket(mult)
                if 0 <= idx < 5:
                    buf[base + idx] = 1.0
            base += 5
            # ── disabled / cannot-select ──.
            if m is not None:
                disabled = ((m.pp or 0) <= 0
                            or (getattr(p, "disable", None)
                                and p.disable.active()
                                and getattr(p.disable, "item", None) is m))
                buf[base + 0] = 1.0 if disabled else 0.0
            base += 1

            move_off = base
        cur = move_off
    else:
        cur += F.POKE_BLOCK.move_block


def _write_field_block(buf: np.ndarray, off: int, battle, ours, theirs) -> None:
    if battle is None:
        return
    cur = off

    wname = ""
    try:
        wname = battle.weather.get() or ""
    except Exception:
        pass
    buf[cur + F.weather_index(wname)] = 1.0
    cur += F.N_WEATHER

    tname = ""
    try:
        tname = battle.terrain.item or ""
    except Exception:
        pass
    buf[cur + F.terrain_index(tname)] = 1.0
    cur += F.N_TERRAIN

    buf[cur] = _expiring_turns(battle.weather)
    cur += 1
    buf[cur] = _expiring_turns(battle.terrain)
    cur += 1

    for room in (battle.trick_room, battle.gravity,
                 battle.magic_room, battle.wonder_room):
        buf[cur + 0] = _expiring_active(room)
        buf[cur + 1] = _expiring_turns(room)
        cur += 2

    for side in (ours, theirs):
        if side is None:
            cur += (F.FIELD_BLOCK.side_hazards_each
                    + F.FIELD_BLOCK.side_screens_each
                    + F.FIELD_BLOCK.side_misc_each)
            continue
        buf[cur + 0] = (getattr(side, "spikes", 0) or 0) / 3.0
        buf[cur + 1] = (getattr(side, "toxic_spikes", 0) or 0) / 2.0
        buf[cur + 2] = 1.0 if getattr(side, "stealth_rock", False) else 0.0
        buf[cur + 3] = 1.0 if getattr(side, "sticky_web", False) else 0.0
        buf[cur + 4] = 0.0
        cur += F.FIELD_BLOCK.side_hazards_each
        buf[cur + 0] = _expiring_turns(getattr(side, "light_screen", None))
        buf[cur + 1] = _expiring_turns(getattr(side, "reflect", None))
        buf[cur + 2] = _expiring_turns(getattr(side, "aurora_veil", None))
        buf[cur + 3] = _expiring_turns(getattr(side, "safeguard", None))
        cur += F.FIELD_BLOCK.side_screens_each
        buf[cur + 0] = _expiring_turns(getattr(side, "tailwind", None))
        buf[cur + 1] = _expiring_turns(getattr(side, "mist", None))
        buf[cur + 2] = _expiring_turns(getattr(side, "mud_sport", None))
        buf[cur + 3] = _expiring_turns(getattr(side, "water_sport", None))
        buf[cur + 4] = 1.0 if (getattr(side, "future_sight", None)
                                 and getattr(side.future_sight, "active", lambda: False)()) else 0.0
        buf[cur + 5] = 1.0 if getattr(side, "healing_wish", False) else 0.0
        cur += F.FIELD_BLOCK.side_misc_each

    buf[cur] = 1.0 if getattr(battle, "inverse_battle", False) else 0.0
    cur += 1
    buf[cur] = min(1.0, (getattr(battle, "turn", 0) or 0) / 100.0)
    cur += 1
    buf[cur] = 1.0 if getattr(battle, "plasma_fists", False) else 0.0
    cur += 1
    lme = getattr(battle, "last_move_effect", None)
    buf[cur] = 1.0 if lme is not None else 0.0
    cur += 1


def _write_global_block(buf: np.ndarray, off: int, battle, ours, theirs) -> None:
    if ours is None or theirs is None:
        return

    def _alive(t):
        return sum(1 for p in (t.party or []) if (p.hp or 0) > 0)

    def _hp_total(t):
        return sum(max(0, p.hp or 0) for p in (t.party or []))

    def _hp_starting(t):
        return sum(max(1, p.starting_hp or 1) for p in (t.party or []))

    our_alive    = _alive(ours)
    opp_alive    = _alive(theirs)
    our_hp_share = _hp_total(ours) / max(1, _hp_total(ours) + _hp_total(theirs))
    avg_hp_ours  = _hp_total(ours)   / max(1, _hp_starting(ours))
    avg_hp_opp   = _hp_total(theirs) / max(1, _hp_starting(theirs))

    cur = off
    buf[cur] = float(our_hp_share)
    cur += 1
    buf[cur] = (our_alive - opp_alive + 6) / 12.0
    cur += 1
    buf[cur] = float(avg_hp_ours - avg_hp_opp + 1.0) / 2.0
    cur += 1
    # Speed dominance one-hot.
    speed_dom = 1
    try:
        sa = ours.current_pokemon.get_speed(battle) if ours.current_pokemon else 0
        sb = theirs.current_pokemon.get_speed(battle) if theirs.current_pokemon else 0
        if sa > sb:   speed_dom = 0
        elif sa < sb: speed_dom = 2
    except Exception:
        pass
    buf[cur + speed_dom] = 1.0
    cur += 3
    try:
        cur_us = ours.current_pokemon
        cur_op = theirs.current_pokemon
        setup_us = sum([getattr(cur_us, k, 0) for k in (
            "attack_stage", "defense_stage", "spatk_stage",
            "spdef_stage", "speed_stage")]) if cur_us else 0
        setup_op = sum([getattr(cur_op, k, 0) for k in (
            "attack_stage", "defense_stage", "spatk_stage",
            "spdef_stage", "speed_stage")]) if cur_op else 0
        b = max(0, min(5, (setup_us - setup_op + 6) // 2))
        buf[cur + b] = 1.0
    except Exception:
        pass
    cur += 6
    try:
        our_haz = (ours.spikes or 0) + (ours.toxic_spikes or 0) + int(ours.stealth_rock) + int(ours.sticky_web)
        opp_haz = (theirs.spikes or 0) + (theirs.toxic_spikes or 0) + int(theirs.stealth_rock) + int(theirs.sticky_web)
        b = max(0, min(5, (opp_haz - our_haz + 4) // 2))
        buf[cur + b] = 1.0
    except Exception:
        pass
    cur += 6
    try:
        revealed_us = sum(1 for p in ours.party if getattr(p, "ever_sent_out", False))
        revealed_op = sum(1 for p in theirs.party if getattr(p, "ever_sent_out", False))
        buf[cur] = revealed_us / max(1, len(ours.party))
        cur += 1
        buf[cur] = revealed_op / max(1, len(theirs.party))
        cur += 1
    except Exception:
        cur += 2


class BattleEncoder:
    """Encode a battle from the point of view of *us*.

    The encoder is stateful only through a ``HiddenInfoTracker`` that the
    caller is expected to feed with observations as the battle unfolds; see
    ``ai/hidden_info.py`` for the contract.
    """

    __slots__ = ("hidden",)

    def __init__(self, hidden: Optional[HiddenInfoTracker] = None) -> None:
        self.hidden = hidden or HiddenInfoTracker()

    def encode(self, battle, us, them, *, history=None) -> np.ndarray:
        """Return a fresh ``np.ndarray[float32]`` of shape ``(FEATURE_DIM,)``."""
        buf = np.zeros(F.FEATURE_DIM, dtype=np.float32)

        if battle is not None and them is not None:
            try:
                self.hidden.observe(battle, us, them)
            except Exception:
                pass

        if us is not None:
            active = us.current_pokemon
            _write_poke_block(buf, F.ACTIVE_OURS_OFFSET, active,
                              visible=True,
                              opponent_active=(them.current_pokemon if them else None),
                              battle=battle)
            bench_idx = 0
            for poke in us.party:
                if poke is active:
                    continue
                if bench_idx >= F.TEAM_SIZE - 1:
                    break
                off = F.BENCH_OURS_OFFSET + bench_idx * F.POKE_BLOCK_SIZE
                _write_poke_block(buf, off, poke, visible=True,
                                  opponent_active=(them.current_pokemon if them else None),
                                  battle=battle, slot_idx=bench_idx)
                bench_idx += 1

        if them is not None:
            opp_active = them.current_pokemon
            _write_poke_block(buf, F.ACTIVE_OPP_OFFSET, opp_active,
                              visible=opp_active is not None,
                              opponent_active=(us.current_pokemon if us else None),
                              battle=battle,
                              hidden=self.hidden)
            bench_idx = 0
            for poke in them.party:
                if poke is opp_active:
                    continue
                if bench_idx >= F.TEAM_SIZE - 1:
                    break
                off = F.BENCH_OPP_OFFSET + bench_idx * F.POKE_BLOCK_SIZE
                # Bench pokes are only "visible" once they have been on the field at some point.
                visible = bool(getattr(poke, "ever_sent_out", False))
                _write_poke_block(buf, off, poke, visible=visible,
                                  opponent_active=(us.current_pokemon if us else None),
                                  battle=battle, hidden=self.hidden,
                                  slot_idx=bench_idx)
                bench_idx += 1

        _write_field_block(buf, F.FIELD_OFFSET, battle, us, them)
        _write_global_block(buf, F.GLOBAL_OFFSET, battle, us, them)

        self.hidden.write(buf, F.HIDDEN_OFFSET, them)

        if history is not None:
            history.write(buf, F.HISTORY_OFFSET)

        return buf


__all__ = ["BattleEncoder"]
