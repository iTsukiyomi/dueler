from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from . import features as F


ITEM_BUCKETS = [
    "choice-band", "choice-scarf", "choice-specs",
    "life-orb", "leftovers", "focus-sash",
    "heavy-duty-boots", "booster-energy",
    "assault-vest", "eviolite", "rocky-helmet",
    "unknown",
]
_ITEM_INDEX = {n: i for i, n in enumerate(ITEM_BUCKETS)}

MOVE_ARCHETYPES = [
    "stab", "coverage", "status", "setup", "pivot", "hazards",
    "recovery", "priority", "screens", "weather", "terrain",
    "trapping", "trick-room", "defog", "taunt", "speed-control",
]
_MOVE_ARCH_INDEX = {n: i for i, n in enumerate(MOVE_ARCHETYPES)}

SET_ARCHETYPES = [
    "sweeper", "wall", "pivot", "lead",
    "breaker", "support", "mixed", "unknown",
]
_SET_ARCH_INDEX = {n: i for i, n in enumerate(SET_ARCHETYPES)}


HAZARD_EFFECTS    = {34, 38, 39, 372, 446}
RECOVERY_EFFECTS  = {33, 215, 357, 397}
PIVOT_EFFECTS     = {28, 314, 230, 442}
SETUP_EFFECTS     = {18, 51, 30, 198, 224, 277, 280, 374, 348}
DEFOG_EFFECTS     = {261, 343}
TAUNT_EFFECTS     = {103, 285, 286}
STATUS_EFFECTS    = {7, 8, 9, 32, 35, 36, 67, 78, 84, 87, 137, 150}
SCREEN_EFFECTS    = {73, 74, 271, 365}
WEATHER_EFFECTS   = {116, 117, 152, 153, 213, 224}
TERRAIN_EFFECTS   = {439, 440, 441, 481}
TRICK_ROOM_EFFECT = 197
TRAP_EFFECTS      = {43, 252, 175}
SPEED_CONTROL_EFF = {220, 222, 219}


def _classify_move(move) -> List[str]:
    """Return zero or more archetype tags for a given Move object.
    Robust against partially constructed moves."""
    tags: List[str] = []
    eff = int(getattr(move, "effect", 0) or 0)
    dc  = int(getattr(move, "damage_class", 0) or 0)
    pw  = int(getattr(move, "power", 0) or 0)
    pri = int(getattr(move, "priority", 0) or 0)
    name = getattr(move, "name", "") or ""

    if eff == TRICK_ROOM_EFFECT:
        tags.append("trick-room")
    if eff in DEFOG_EFFECTS:
        tags.append("defog")
    if eff in HAZARD_EFFECTS:
        tags.append("hazards")
    if eff in RECOVERY_EFFECTS:
        tags.append("recovery")
    if eff in PIVOT_EFFECTS:
        tags.append("pivot")
    if eff in SETUP_EFFECTS:
        tags.append("setup")
    if eff in SCREEN_EFFECTS:
        tags.append("screens")
    if eff in WEATHER_EFFECTS:
        tags.append("weather")
    if eff in TERRAIN_EFFECTS:
        tags.append("terrain")
    if eff in TRAP_EFFECTS:
        tags.append("trapping")
    if eff in TAUNT_EFFECTS:
        tags.append("taunt")
    if eff in STATUS_EFFECTS or dc == 1 and pw == 0 and not tags:
        tags.append("status")
    if eff in SPEED_CONTROL_EFF:
        tags.append("speed-control")
    if pri > 0 and pw > 0:
        tags.append("priority")
    if pw > 0 and not tags:
        tags.append("stab")
    if pw > 0 and dc != 1:
        tags.append("coverage")

    if not tags:
        tags.append("unknown") if "unknown" in _MOVE_ARCH_INDEX else tags.append("status")
    return tags


@dataclass
class _PokeBelief:
    item:        np.ndarray = field(default_factory=lambda: np.ones(F.HIDDEN_BLOCK.item_buckets,    dtype=np.float32))
    moves:       np.ndarray = field(default_factory=lambda: np.ones(F.HIDDEN_BLOCK.move_set_buckets, dtype=np.float32))
    tera:        np.ndarray = field(default_factory=lambda: np.ones(F.HIDDEN_BLOCK.tera_type_oh,    dtype=np.float32))
    speed_tier:  np.ndarray = field(default_factory=lambda: np.ones(F.HIDDEN_BLOCK.speed_tier_oh,   dtype=np.float32))
    archetype:   np.ndarray = field(default_factory=lambda: np.ones(F.HIDDEN_BLOCK.set_archetype,   dtype=np.float32))
    revealed:    bool = False

    def normalize(self) -> None:
        for arr in (self.item, self.moves, self.tera, self.speed_tier, self.archetype):
            s = float(arr.sum())
            if s > 0:
                arr /= s

    def reveal_item(self, item_name: str) -> None:
        idx = _ITEM_INDEX.get(item_name, _ITEM_INDEX["unknown"])
        self.item[:] = 0.05
        self.item[idx] = 1.0
        self.normalize()

    def reveal_move(self, move) -> None:
        for tag in _classify_move(move):
            i = _MOVE_ARCH_INDEX.get(tag)
            if i is not None:
                self.moves[i] += 3.0
        self.normalize()

    def reveal_tera(self, type_idx: int) -> None:
        if 0 <= type_idx < self.tera.size:
            self.tera[:] = 0.05
            self.tera[type_idx] = 1.0
            self.normalize()

    def reveal_speed(self, speed: float) -> None:
        bins = self.speed_tier.size
        bucket = min(bins - 1, max(0, int(speed) // (700 // bins)))
        self.speed_tier[bucket] += 5.0
        self.normalize()

    def write(self, buf: np.ndarray, off: int) -> int:
        """Write this belief into ``buf`` and return the new offset."""
        for src in (self.item, self.moves, self.tera, self.speed_tier, self.archetype):
            buf[off:off + src.size] = src
            off += src.size
        return off


class HiddenInfoTracker:
    """Maintain belief over each of the six opponent Pokémon.

    The encoder calls ``observe(battle, us, them)`` exactly once per encoder
    step before reading the per-Pokémon beliefs back via ``write``.
    """

    def __init__(self) -> None:
        self._beliefs: List[_PokeBelief] = [_PokeBelief() for _ in range(F.TEAM_SIZE)]
        for b in self._beliefs:
            b.normalize()
        self._last_active_id: Optional[int] = None

    def reset(self) -> None:
        for b in self._beliefs:
            b.__init__()
            b.normalize()
        self._last_active_id = None

    def _belief_for(self, slot: int) -> _PokeBelief:
        if slot < 0 or slot >= F.TEAM_SIZE:
            slot = max(0, min(F.TEAM_SIZE - 1, slot))
        return self._beliefs[slot]

    def observe(self, battle, us, them) -> None:
        """Pull every observable fact from the live battle into the belief."""
        if them is None:
            return
        party = list(them.party or [])
        for slot, poke in enumerate(party[:F.TEAM_SIZE]):
            b = self._belief_for(slot)
            if not getattr(poke, "ever_sent_out", False):
                # Even un-revealed pokes leak species — boost a coarse archetype prior based on base-stat totals.
                self._prior_from_species(poke, b)
                continue
            b.revealed = True

            try:
                hi = getattr(poke, "held_item", None)
                name = getattr(hi, "name", None) if hi is not None else None
                if name:
                    b.reveal_item(name)
            except Exception:
                pass

            try:
                for m in getattr(poke, "moves", None) or ():
                    if m and (m.starting_pp or 0) > (m.pp or 0):
                        b.reveal_move(m)
            except Exception:
                pass

            tera = getattr(poke, "tera_type", None)
            if tera is not None:
                try:
                    b.reveal_tera(int(tera))
                except Exception:
                    pass

            # Speed estimate.
            try:
                spd = poke.get_speed(battle) if battle else poke.get_raw_speed()
                b.reveal_speed(float(spd or 0))
            except Exception:
                pass

            self._prior_from_species(poke, b)

    @staticmethod
    def _prior_from_species(poke, b: _PokeBelief) -> None:
        if poke is None:
            return
        try:
            atk  = poke.attack
            spa  = poke.spatk
            spd  = poke.spdef
            df   = poke.defense
            spe  = poke.speed
            hp   = poke.starting_hp
        except Exception:
            return
        bulk = (hp or 0) + (df or 0) + (spd or 0)
        off  = max(atk or 0, spa or 0)
        if bulk > 750 and off < 100:
            b.archetype[_SET_ARCH_INDEX["wall"]] += 1.5
        elif (spe or 0) >= 110 and off >= 110:
            b.archetype[_SET_ARCH_INDEX["sweeper"]] += 1.5
        elif (spe or 0) >= 110 and off < 100:
            b.archetype[_SET_ARCH_INDEX["pivot"]] += 1.0
        elif off >= 130:
            b.archetype[_SET_ARCH_INDEX["breaker"]] += 1.5
        else:
            b.archetype[_SET_ARCH_INDEX["mixed"]] += 0.5
        b.normalize()

    def write(self, buf: np.ndarray, off: int, them) -> None:
        cur = off
        n = len(them.party) if them and them.party else 0
        for slot in range(F.TEAM_SIZE):
            b = self._belief_for(slot) if slot < n else _PokeBelief()
            cur = b.write(buf, cur)


__all__ = ["HiddenInfoTracker", "ITEM_BUCKETS", "MOVE_ARCHETYPES", "SET_ARCHETYPES"]
