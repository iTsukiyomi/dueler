"""
ai/features.py — Definition of the feature layout produced by encoder.py.

Centralising the layout here lets the encoder, action-mask, hidden-info
estimator and the neural network all agree on the exact positions of every
field. Add a new feature → bump the constants below.

The vector is a flat float32 array of length ``FEATURE_DIM`` and is built
in five sections so that humans (and TensorBoard) can read it.

Order of sections
─────────────────
1. ACTIVE_OURS         (per-Pokémon)
2. BENCH_OURS          (5 slots × per-Pokémon)
3. ACTIVE_OPP          (per-Pokémon, with hidden-info masking)
4. BENCH_OPP           (5 slots × per-Pokémon, mostly hidden)
5. FIELD               (global + side conditions)
6. HIDDEN_INFO_PROBS   (item / move / tera probabilities)
7. HISTORY             (last-N turn rollup)

Constants exposed
─────────────────
- N_SPECIES         : 1100   (Pokémon DB has ≤ ~1025 forms)
- N_ABILITIES       : 350
- N_ITEMS           : 250
- N_MOVES           : 950
- N_TYPES           : 19     (Normal..Fairy + Typeless)
- N_STATUSES        : 7
- MOVES_PER_POKE    : 4
- TEAM_SIZE         : 6
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Cardinalities
# ─────────────────────────────────────────────────────────────────────────────
N_SPECIES         = 1100
N_ABILITIES       = 350
N_ITEMS           = 250
N_MOVES           = 950
N_TYPES           = 19
N_DAMAGE_CLASS    = 4              # 0 unknown, 1 status, 2 physical, 3 special
N_STATUSES        = 7              # none, burn, freeze, paralysis, poison, b-poison, sleep
N_WEATHER         = 8              # none, rain, sun, hail, sandstorm, h-rain, h-sun, h-wind
N_TERRAIN         = 5              # none, electric, grassy, misty, psychic
MOVES_PER_POKE    = 4
TEAM_SIZE         = 6


# ─────────────────────────────────────────────────────────────────────────────
# Sub-feature sizes (per Pokémon)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class _PokeBlock:
    species_oh: int  = 64            # bucket of species id (we hash to N_SPECIES then bucket)
    type_oh:    int  = N_TYPES
    tera_oh:    int  = N_TYPES
    ability_oh: int  = 32            # bucket of ability id
    item_oh:    int  = 32            # bucket of item id
    status_oh: int   = N_STATUSES
    hp:        int   = 1
    stats:     int   = 6             # raw hp/atk/def/spa/spd/spe normalised
    stages:    int   = 7             # atk/def/spa/spd/spe/acc/eva stages
    flags:     int   = 24            # fainted, mega-evolved, can-mega, has-substitute, leech-seed, etc.
    move_block: int  = MOVES_PER_POKE * (
        # per move: type one-hot + damage class + power + accuracy + priority
        # + pp_left/pp_max + STAB + effectiveness vs opponent (5 buckets) + disabled
        N_TYPES + N_DAMAGE_CLASS + 1 + 1 + 1 + 2 + 1 + 5 + 1
    )

    @property
    def size(self) -> int:
        return (self.species_oh + self.type_oh + self.tera_oh
                + self.ability_oh + self.item_oh + self.status_oh
                + self.hp + self.stats + self.stages + self.flags
                + self.move_block)


POKE_BLOCK = _PokeBlock()
POKE_BLOCK_SIZE = POKE_BLOCK.size           # ≈ 360


@dataclass(frozen=True)
class _FieldBlock:
    weather: int          = N_WEATHER
    terrain: int          = N_TERRAIN
    weather_turns: int    = 1
    terrain_turns: int    = 1
    trick_room: int       = 2            # active flag + remaining_turns/8
    gravity: int          = 2
    magic_room: int       = 2
    wonder_room: int      = 2
    side_hazards_each: int = 5           # spikes/3, t-spikes/2, stealth_rock, sticky_web, ?reserved
    side_screens_each: int = 4           # light/reflect/aurora/safeguard turns/8
    side_misc_each: int    = 6           # tailwind, mist, mud_sport, water_sport, future_sight, healing_wish
    inverse: int          = 1
    turn: int             = 1            # turn/100
    plasma_fists: int     = 1
    last_move_effect: int = 1

    @property
    def size(self) -> int:
        return (self.weather + self.terrain
                + self.weather_turns + self.terrain_turns
                + self.trick_room + self.gravity + self.magic_room + self.wonder_room
                + 2 * (self.side_hazards_each + self.side_screens_each + self.side_misc_each)
                + self.inverse + self.turn + self.plasma_fists + self.last_move_effect)


FIELD_BLOCK = _FieldBlock()
FIELD_BLOCK_SIZE = FIELD_BLOCK.size


@dataclass(frozen=True)
class _HiddenBlock:
    # Probabilities the opponent's revealed Pokémon holds each common item bucket
    item_buckets: int        = 12          # choice scarf/band/specs/sash/lefties/life-orb/heavy-duty/booster/etc.
    move_set_buckets: int    = 16          # setup, recovery, hazards, status, pivot, priority, etc.
    tera_type_oh: int        = N_TYPES     # estimated tera type distribution
    speed_tier_oh: int       = 8           # binned predicted base-speed tier
    set_archetype: int       = 8           # sweeper / wall / pivot / lead / breaker / utility / mixed / unknown

    @property
    def per_poke(self) -> int:
        return (self.item_buckets + self.move_set_buckets
                + self.tera_type_oh + self.speed_tier_oh + self.set_archetype)

    @property
    def size(self) -> int:
        return TEAM_SIZE * self.per_poke


HIDDEN_BLOCK = _HiddenBlock()
HIDDEN_BLOCK_SIZE = HIDDEN_BLOCK.size


@dataclass(frozen=True)
class _HistoryBlock:
    last_turns: int          = 4            # remember 4 previous turns
    per_turn: int            = 16           # (our move-type / hit / our switched / opp switched / dmg dealt / dmg taken / status applied / crit / missed / koed / opp-koed / mega / weather-changed / terrain-changed / setup / hazards-set)

    @property
    def size(self) -> int:
        return self.last_turns * self.per_turn


HISTORY_BLOCK = _HistoryBlock()
HISTORY_BLOCK_SIZE = HISTORY_BLOCK.size


@dataclass(frozen=True)
class _GlobalBlock:
    """Compact global summary so the network sees momentum at a glance."""
    momentum: int         = 1      # our hp share / total hp
    alive_diff: int       = 1
    avg_hp_diff: int      = 1
    speed_dom: int        = 3      # we faster / equal / slower (one-hot)
    setup_dom: int        = 6      # our setup stages summed - opp's (binned 6)
    hazard_dom: int       = 6      # our hazards - opp hazards bins
    revealed_frac_us: int = 1
    revealed_frac_op: int = 1

    @property
    def size(self) -> int:
        return (self.momentum + self.alive_diff + self.avg_hp_diff
                + self.speed_dom + self.setup_dom + self.hazard_dom
                + self.revealed_frac_us + self.revealed_frac_op)


GLOBAL_BLOCK = _GlobalBlock()
GLOBAL_BLOCK_SIZE = GLOBAL_BLOCK.size


# ─────────────────────────────────────────────────────────────────────────────
# Offsets into the final flat vector
# ─────────────────────────────────────────────────────────────────────────────
ACTIVE_OURS_OFFSET = 0
ACTIVE_OURS_END    = ACTIVE_OURS_OFFSET + POKE_BLOCK_SIZE

BENCH_OURS_OFFSET  = ACTIVE_OURS_END
BENCH_OURS_END     = BENCH_OURS_OFFSET + (TEAM_SIZE - 1) * POKE_BLOCK_SIZE

ACTIVE_OPP_OFFSET  = BENCH_OURS_END
ACTIVE_OPP_END     = ACTIVE_OPP_OFFSET + POKE_BLOCK_SIZE

BENCH_OPP_OFFSET   = ACTIVE_OPP_END
BENCH_OPP_END      = BENCH_OPP_OFFSET + (TEAM_SIZE - 1) * POKE_BLOCK_SIZE

FIELD_OFFSET       = BENCH_OPP_END
FIELD_END          = FIELD_OFFSET + FIELD_BLOCK_SIZE

HIDDEN_OFFSET      = FIELD_END
HIDDEN_END         = HIDDEN_OFFSET + HIDDEN_BLOCK_SIZE

HISTORY_OFFSET     = HIDDEN_END
HISTORY_END        = HISTORY_OFFSET + HISTORY_BLOCK_SIZE

GLOBAL_OFFSET      = HISTORY_END
GLOBAL_END         = GLOBAL_OFFSET + GLOBAL_BLOCK_SIZE

FEATURE_DIM        = GLOBAL_END


# ─────────────────────────────────────────────────────────────────────────────
# Lookup helpers (consistent bucket-hashing of integer ids)
# ─────────────────────────────────────────────────────────────────────────────
def bucket(idx: int | None, total_buckets: int, max_id: int) -> int:
    """Hash an integer id into ``total_buckets`` deterministic slots.

    ``None`` (or 0 / negative) maps to bucket 0 — the "unknown" slot.
    """
    if idx is None or idx <= 0:
        return 0
    return 1 + ((int(idx) - 1) * (total_buckets - 1) // max(1, max_id - 1))


def status_index(name: str | None) -> int:
    return {
        "":           0,
        None:         0,
        "burn":       1,
        "freeze":     2,
        "paralysis":  3,
        "poison":     4,
        "b-poison":   5,
        "sleep":      6,
    }.get(name, 0)


def weather_index(name: str | None) -> int:
    return {
        "":          0,
        None:        0,
        "rain":      1,
        "sun":       2,
        "hail":      3,
        "sandstorm": 4,
        "h-rain":    5,
        "h-sun":     6,
        "h-wind":    7,
    }.get(name, 0)


def terrain_index(name: str | None) -> int:
    return {
        "":         0,
        None:       0,
        "electric": 1,
        "grassy":   2,
        "misty":    3,
        "psychic":  4,
    }.get(name, 0)


def offsets_for_poke(slot_kind: str, slot_idx: int) -> Tuple[int, int]:
    """Return ``(start, end)`` indices for the given Pokémon slot."""
    if slot_kind == "ours_active":
        return ACTIVE_OURS_OFFSET, ACTIVE_OURS_END
    if slot_kind == "ours_bench":
        s = BENCH_OURS_OFFSET + slot_idx * POKE_BLOCK_SIZE
        return s, s + POKE_BLOCK_SIZE
    if slot_kind == "opp_active":
        return ACTIVE_OPP_OFFSET, ACTIVE_OPP_END
    if slot_kind == "opp_bench":
        s = BENCH_OPP_OFFSET + slot_idx * POKE_BLOCK_SIZE
        return s, s + POKE_BLOCK_SIZE
    raise ValueError(slot_kind)


__all__ = [
    "FEATURE_DIM", "POKE_BLOCK_SIZE", "FIELD_BLOCK_SIZE",
    "HIDDEN_BLOCK_SIZE", "HISTORY_BLOCK_SIZE", "GLOBAL_BLOCK_SIZE",
    "ACTIVE_OURS_OFFSET", "BENCH_OURS_OFFSET", "ACTIVE_OPP_OFFSET",
    "BENCH_OPP_OFFSET", "FIELD_OFFSET", "HIDDEN_OFFSET",
    "HISTORY_OFFSET", "GLOBAL_OFFSET",
    "N_SPECIES", "N_ABILITIES", "N_ITEMS", "N_MOVES", "N_TYPES",
    "N_DAMAGE_CLASS", "N_STATUSES", "N_WEATHER", "N_TERRAIN",
    "MOVES_PER_POKE", "TEAM_SIZE",
    "bucket", "status_index", "weather_index", "terrain_index",
    "offsets_for_poke", "POKE_BLOCK", "FIELD_BLOCK", "HIDDEN_BLOCK",
    "HISTORY_BLOCK", "GLOBAL_BLOCK",
]
