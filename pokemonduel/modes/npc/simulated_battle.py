"""
simulated_battle.py  ─  Headless pre-training for the DQN AI.

Runs thousands of realistic Pokémon battles without Discord/async.
The SimPokemon / SimTrainer / SimBattle interfaces exactly mirror the real
DuelPokemon / Trainer / Battle objects so the DQN's _encode() method works
unchanged on both simulated and real data.

Run directly to pre-train:
    python simulated_battle.py [--battles N] [--verbose]

Recommended: run 2000+ battles before your first real session.
"""
from __future__ import annotations
import os, sys, random, time, argparse
import numpy as np

# ── DQN core (no game deps) ──────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _dqn_core import (
    DQNetwork, ReplayBuffer,
    Q_NET_PATH, TGT_NET_PATH, BUFFER_PATH, STATS_PATH,
    N_FEATURES, N_ACTIONS, LR, GAMMA,
    EPS_START, EPS_END, EPS_DECAY,
    TGT_UPDATE, BATCH_SZ, MIN_BUF, SAVE_FREQ, show_progress,
    STEPS_PER_TURN, STEPS_PER_END,
)

# ═════════════════════════════════════════════════════════════════════════════
# Type system  (IDs match the game DB: Normal=1 Fire=10 Water=11 … Fairy=18)
# ═════════════════════════════════════════════════════════════════════════════
TYPE_ID = {
    "normal":   1, "fighting": 2, "flying":  3, "poison": 4,
    "ground":   5, "rock":     6, "bug":     7, "ghost":  8,
    "steel":    9, "fire":    10, "water":  11, "grass":  12,
    "electric":13, "psychic": 14, "ice":    15, "dragon": 16,
    "dark":    17, "fairy":   18,
}
TYPE_NAMES = {v: k for k, v in TYPE_ID.items()}

# Full Gen-6+ type chart: {(atk_id, def_id): damage_factor}
# damage_factor  200=2x  100=1x  50=0.5x  0=immune
# Omitted pairs default to 100 (neutral)
_RAW_CHART = {
    # Normal
    (1,8):0,(1,9):50,
    # Fighting
    (2,1):200,(2,6):200,(2,8):0,(2,9):200,(2,14):50,
    (2,3):50,(2,4):50,(2,7):50,(2,17):200,(2,18):50,
    # Flying
    (3,2):200,(3,12):200,(3,7):200,(3,9):50,(3,6):50,(3,13):50,
    # Poison
    (4,12):200,(4,18):200,(4,4):50,(4,5):50,(4,6):50,(4,8):50,(4,9):0,
    # Ground
    (5,10):200,(5,13):200,(5,4):200,(5,6):200,(5,9):200,
    (5,3):0,(5,12):50,(5,7):50,
    # Rock
    (6,10):200,(6,15):200,(6,3):200,(6,7):200,(6,9):50,
    (6,2):50,(6,5):50,
    # Bug
    (7,12):200,(7,14):200,(7,17):200,(7,10):50,(7,3):50,
    (7,2):50,(7,18):50,(7,9):50,(7,8):50,
    # Ghost
    (8,1):0,(8,14):200,(8,17):200,(8,8):50,
    # Steel
    (9,15):200,(9,18):200,(9,6):200,(9,9):50,(9,10):50,(9,11):50,
    (9,13):50,(9,2):50,(9,5):50,
    # Fire
    (10,12):200,(10,15):200,(10,7):200,(10,9):200,
    (10,10):50,(10,11):50,(10,6):50,(10,16):50,
    # Water
    (11,10):200,(11,5):200,(11,6):200,
    (11,11):50,(11,12):50,(11,16):50,
    # Grass
    (12,11):200,(12,5):200,(12,6):200,
    (12,10):50,(12,12):50,(12,4):50,(12,3):50,(12,7):50,(12,16):50,
    # Electric
    (13,11):200,(13,3):200,
    (13,5):0,(13,12):50,(13,13):50,(13,16):50,
    # Psychic
    (14,2):200,(14,4):200,
    (14,9):50,(14,14):50,(14,17):0,
    # Ice
    (15,12):200,(15,5):200,(15,3):200,(15,16):200,
    (15,9):50,(15,11):50,(15,15):50,
    # Dragon
    (16,16):200,(16,9):50,(16,18):0,
    # Dark
    (17,14):200,(17,8):200,
    (17,2):50,(17,18):50,(17,17):50,
    # Fairy
    (18,2):200,(18,16):200,(18,17):200,
    (18,10):50,(18,4):50,(18,9):50,
}

def _eff(atk_id: int, def_id: int) -> int:
    return _RAW_CHART.get((atk_id, def_id), 100)

def _matchup(move_type_id: int, defender_type_ids: list[int]) -> float:
    factor = 1.0
    for dt in defender_type_ids:
        factor *= _eff(move_type_id, dt) / 100.0
    return factor


# ═════════════════════════════════════════════════════════════════════════════
# Pokémon move database — realistic competitive moves
# ═════════════════════════════════════════════════════════════════════════════
class SimDC:
    """Mirrors DamageClass enum without importing game code."""
    STATUS   = "status"
    PHYSICAL = "physical"
    SPECIAL  = "special"

_MOVES_DB = [
    # name                   type_id  pw   acc  prio  dc              effect
    # ─ Physical ─────────────────────────────────────────────────────────────
    ("close-combat",        2, 120, 100, 0, SimDC.PHYSICAL, None),
    ("earthquake",          5, 100, 100, 0, SimDC.PHYSICAL, None),
    ("stone-edge",          6, 100,  80, 0, SimDC.PHYSICAL, None),
    ("iron-head",           9,  80, 100, 0, SimDC.PHYSICAL, None),
    ("u-turn",              7,  70, 100, 0, SimDC.PHYSICAL, "pivot"),
    ("x-scissor",           7,  80, 100, 0, SimDC.PHYSICAL, None),
    ("poison-jab",          4,  80, 100, 0, SimDC.PHYSICAL, None),
    ("play-rough",         18,  90,  90, 0, SimDC.PHYSICAL, None),
    ("body-slam",           1,  85, 100, 0, SimDC.PHYSICAL, None),
    ("waterfall",          11,  80, 100, 0, SimDC.PHYSICAL, None),
    ("ice-punch",          15,  75, 100, 0, SimDC.PHYSICAL, None),
    ("thunder-punch",      13,  75, 100, 0, SimDC.PHYSICAL, None),
    ("fire-punch",         10,  75, 100, 0, SimDC.PHYSICAL, None),
    ("wicked-blow",        17,  80, 100, 0, SimDC.PHYSICAL, "crit"),
    ("sunsteel-strike",     9, 100, 100, 0, SimDC.PHYSICAL, None),
    ("outrage",            16, 120, 100, 0, SimDC.PHYSICAL, None),
    ("crabhammer",         11, 100,  90, 0, SimDC.PHYSICAL, None),
    ("high-horsepower",     5,  95,  95, 0, SimDC.PHYSICAL, None),
    ("scale-shot",         16,  25,  90, 0, SimDC.PHYSICAL, None),
    ("sucker-punch",       17,  70, 100, 1, SimDC.PHYSICAL, "priority"),
    ("mach-punch",          2,  40, 100, 1, SimDC.PHYSICAL, "priority"),
    ("aqua-jet",           11,  40, 100, 1, SimDC.PHYSICAL, "priority"),
    ("bullet-punch",        9,  40, 100, 1, SimDC.PHYSICAL, "priority"),
    ("extreme-speed",       1,  80, 100, 2, SimDC.PHYSICAL, "priority"),
    ("swords-dance",        1,   0, 100, 0, SimDC.STATUS,   "atk+2"),
    # ─ Special ───────────────────────────────────────────────────────────────
    ("hydro-pump",         11, 110,  80, 0, SimDC.SPECIAL,  None),
    ("surf",               11,  90, 100, 0, SimDC.SPECIAL,  None),
    ("ice-beam",           15,  90, 100, 0, SimDC.SPECIAL,  None),
    ("blizzard",           15, 110,  70, 0, SimDC.SPECIAL,  None),
    ("thunderbolt",        13,  90, 100, 0, SimDC.SPECIAL,  None),
    ("thunder",            13, 110,  70, 0, SimDC.SPECIAL,  None),
    ("flamethrower",       10,  90, 100, 0, SimDC.SPECIAL,  None),
    ("fire-blast",         10, 110,  85, 0, SimDC.SPECIAL,  None),
    ("psychic",            14,  90, 100, 0, SimDC.SPECIAL,  None),
    ("moonblast",          18,  95, 100, 0, SimDC.SPECIAL,  None),
    ("draco-meteor",       16, 130,  90, 0, SimDC.SPECIAL,  None),
    ("dragon-pulse",       16,  85, 100, 0, SimDC.SPECIAL,  None),
    ("aura-sphere",         2,  80, 100, 0, SimDC.SPECIAL,  None),
    ("focus-blast",         2, 120,  70, 0, SimDC.SPECIAL,  None),
    ("shadow-ball",         8,  80, 100, 0, SimDC.SPECIAL,  None),
    ("energy-ball",        12,  90, 100, 0, SimDC.SPECIAL,  None),
    ("sludge-bomb",         4,  90, 100, 0, SimDC.SPECIAL,  None),
    ("flash-cannon",        9,  80, 100, 0, SimDC.SPECIAL,  None),
    ("bug-buzz",            7,  90, 100, 0, SimDC.SPECIAL,  None),
    ("air-slash",           3,  75,  95, 0, SimDC.SPECIAL,  None),
    ("earth-power",         5,  90, 100, 0, SimDC.SPECIAL,  None),
    ("lava-plume",         10,  80, 100, 0, SimDC.SPECIAL,  None),
    ("dark-pulse",         17,  80, 100, 0, SimDC.SPECIAL,  None),
    ("stored-power",       14,  20, 100, 0, SimDC.SPECIAL,  None),
    ("calm-mind",          14,   0, 100, 0, SimDC.STATUS,   "spatk+1"),
    ("nasty-plot",         17,   0, 100, 0, SimDC.STATUS,   "spatk+2"),
    # ─ Status ────────────────────────────────────────────────────────────────
    ("stealth-rock",        6,   0, 100, 0, SimDC.STATUS,  "stealth_rock"),
    ("spikes",              5,   0, 100, 0, SimDC.STATUS,  "spikes"),
    ("toxic-spikes",        4,   0, 100, 0, SimDC.STATUS,  "toxic_spikes"),
    ("toxic",               4,   0,  90, 0, SimDC.STATUS,  "toxic"),
    ("will-o-wisp",        10,   0,  85, 0, SimDC.STATUS,  "burn"),
    ("thunder-wave",       13,   0,  90, 0, SimDC.STATUS,  "paralyze"),
    ("recover",             1,   0, 100, 0, SimDC.STATUS,  "heal"),
    ("roost",               3,   0, 100, 0, SimDC.STATUS,  "heal"),
    ("defog",               3,   0, 100, 0, SimDC.STATUS,  "defog"),
    ("rapid-spin",          1,  50, 100, 0, SimDC.PHYSICAL,"defog"),
    ("encore",              1,   0, 100, 0, SimDC.STATUS,  "encore"),
    ("substitute",          1,   0, 100, 0, SimDC.STATUS,  "sub"),
]

# Build the move objects once
_ALL_MOVES: list["SimMove"] = []

class SimMove:
    __slots__ = ("name","type","power","accuracy","priority","damage_class","effect")
    def __init__(self, name, type_id, power, accuracy, priority, dc, effect):
        self.name         = name
        self.type         = type_id
        self.power        = power
        self.accuracy     = accuracy
        self.priority     = priority
        self.damage_class = dc
        self.effect       = effect

for _row in _MOVES_DB:
    _ALL_MOVES.append(SimMove(*_row))

_MOVES_BY_TYPE: dict[int, list[SimMove]] = {}
for _m in _ALL_MOVES:
    _MOVES_BY_TYPE.setdefault(_m.type, []).append(_m)

# ═════════════════════════════════════════════════════════════════════════════
# SimNV — non-volatile status, mirrors DuelPokemon.nv
# ═════════════════════════════════════════════════════════════════════════════
class SimNV:
    __slots__ = ("burn","paralyze","toxic","poison","sleep","freeze","current","toxic_count")
    def __init__(self):
        self.burn       = False
        self.paralyze   = False
        self.toxic      = False
        self.poison     = False
        self.sleep      = False
        self.freeze     = False
        self.current    = None
        self.toxic_count = 0

    def apply(self, status: str):
        if self.current:
            return  # already statused
        if status == "burn":
            self.burn = True;    self.current = "burn"
        elif status == "paralyze":
            self.paralyze = True;self.current = "paralyze"
        elif status == "toxic":
            self.toxic = True;   self.current = "toxic"
        elif status == "poison":
            self.poison = True;  self.current = "poison"
        elif status == "sleep":
            self.sleep = True;   self.current = "sleep"
        elif status == "freeze":
            self.freeze = True;  self.current = "freeze"

    def clear(self):
        self.__init__()


# ═════════════════════════════════════════════════════════════════════════════
# SimPokemon  — mirrors DuelPokemon interface exactly
# ═════════════════════════════════════════════════════════════════════════════
ALL_TYPES = list(TYPE_ID.values())

# Competitive Pokémon archetypes
_ARCHETYPES = [
    # name_prefix     types              base_stats (hp,atk,def,spa,spd,spe)
    ("Dragonite",    [16, 3],           (91,134,95,100,100,80)),
    ("Garchomp",     [16, 5],           (108,130,95,80,85,102)),
    ("Tyranitar",    [6, 17],           (100,134,110,95,100,61)),
    ("Salamence",    [16, 3],           (95,135,80,110,80,100)),
    ("Metagross",    [9, 14],           (80,135,130,95,90,70)),
    ("Lucario",      [2, 9],            (70,110,70,115,70,90)),
    ("Gyarados",     [11, 3],           (95,125,79,60,100,81)),
    ("Togekiss",     [18, 3],           (85,50,95,120,115,80)),
    ("Gengar",       [8, 4],            (60,65,60,130,75,110)),
    ("Clefable",     [18],              (95,70,73,95,90,60)),
    ("Ferrothorn",   [12, 9],           (74,94,131,54,116,20)),
    ("Heatran",      [10, 9],           (91,90,106,130,106,77)),
    ("Rotom-W",      [13, 11],          (50,65,107,105,107,86)),
    ("Landorus-T",   [5, 3],            (89,145,90,105,80,91)),
    ("Excadrill",    [9, 5],            (110,135,60,50,65,88)),
    ("Cloyster",     [11, 15],          (50,95,180,85,45,70)),
    ("Venusaur",     [12, 4],           (80,82,83,100,100,80)),
    ("Blaziken",     [10, 2],           (80,120,70,110,70,80)),
    ("Swampert",     [11, 5],           (100,110,90,85,90,60)),
    ("Blissey",      [1],               (255,10,10,75,135,55)),
    ("Skarmory",     [9, 3],            (65,80,140,40,70,70)),
    ("Politoed",     [11],              (90,75,75,90,100,70)),
    ("Ninetales",    [10],              (73,76,75,81,100,100)),
    ("Breloom",      [12, 2],           (60,130,80,60,60,70)),
    ("Conkeldurr",   [2],               (105,140,95,55,65,45)),
    ("Infernape",    [10, 2],           (76,104,71,104,71,108)),
    ("Magnezone",    [13, 9],           (70,70,115,130,90,60)),
    ("Gliscor",      [5, 3],            (75,95,125,45,75,95)),
    ("Jellicent",    [11, 8],           (100,60,70,85,105,60)),
    ("Reuniclus",    [14],              (110,65,75,125,85,30)),
    ("Volcarona",    [7, 10],           (85,60,65,135,105,100)),
    ("Urshifu",      [2, 17],           (100,130,100,63,60,97)),
    ("Dragapult",    [16, 8],           (88,120,75,100,75,142)),
    ("Grimmsnarl",   [17, 18],          (95,120,65,95,75,60)),
    ("Rillaboom",    [12],              (100,125,90,60,70,85)),
    ("Cinderace",    [10],              (80,116,75,65,75,119)),
    ("Inteleon",     [11],              (70,85,65,125,65,120)),
    ("Melmetal",     [9],               (135,143,143,80,65,34)),
    ("Toxapex",      [11, 4],           (50,63,152,53,142,35)),
    ("Kartana",      [12, 9],           (59,181,131,59,31,109)),
]

def _rand_moves(poke_types: list[int], n: int = 4) -> list[SimMove]:
    """Give a Pokémon a realistic, competitive moveset."""
    chosen: list[SimMove] = []

    # 1. Always include a STAB physical or special move
    stab_atk = [m for m in _ALL_MOVES
                if m.type in poke_types and m.power > 0 and m.damage_class != SimDC.STATUS]
    if stab_atk:
        chosen.append(random.choice(stab_atk))

    # 2. Coverage move (different type from STAB)
    coverage = [m for m in _ALL_MOVES
                if m.type not in poke_types and m.power > 60
                and m.damage_class != SimDC.STATUS
                and m not in chosen]
    if coverage:
        chosen.append(random.choice(coverage))

    # 3. Maybe a priority or pivot move
    if random.random() < 0.35:
        prio_moves = [m for m in _ALL_MOVES if m.priority > 0 and m not in chosen]
        if prio_moves:
            chosen.append(random.choice(prio_moves))

    # 4. Fill remaining with random (status / more coverage)
    pool = [m for m in _ALL_MOVES if m not in chosen]
    random.shuffle(pool)
    while len(chosen) < n and pool:
        chosen.append(pool.pop())

    return chosen[:n]


class SimPokemon:
    """Mirrors DuelPokemon exactly — _encode() works on this without changes."""

    def __init__(self, name: str, type_ids: list[int],
                 base: tuple, moves: list[SimMove]):
        hp, atk, dfs, spa, spd, spe = base
        # Apply EVs / nature: competitive distribution
        atk = int(atk * random.uniform(0.9, 1.2))
        dfs = int(dfs * random.uniform(0.9, 1.2))
        spa = int(spa * random.uniform(0.9, 1.2))
        spd = int(spd * random.uniform(0.9, 1.2))
        spe = int(spe * random.uniform(0.9, 1.2))
        hp_val = hp + random.randint(10, 30)   # rough lv50 HP formula

        self.name         = name
        self.type_ids     = type_ids
        self.starting_hp  = hp_val
        self.hp           = hp_val
        self.attack       = atk
        self.defense      = dfs
        self.spatk        = spa
        self.spdef        = spd
        self._base_spe    = spe
        self.moves        = moves

        # stage modifiers
        self.attack_stage  = 0
        self.defense_stage = 0
        self.spatk_stage   = 0
        self.spdef_stage   = 0
        self.speed_stage   = 0

        self.nv           = SimNV()
        self.has_moved    = False

    # ── stat accessors that match DuelPokemon ────────────────────────────────
    def _stage_mult(self, stage: int) -> float:
        return max(2, 2 + stage) / max(2, 2 - stage)

    def get_raw_speed(self) -> float:
        return float(self._base_spe)

    def get_speed(self, battle=None) -> float:
        spd = self._base_spe * self._stage_mult(self.speed_stage)
        if self.nv.paralyze:
            spd *= 0.5
        return float(spd)

    def get_attack(self, battle=None) -> float:
        atk = self.attack * self._stage_mult(self.attack_stage)
        if self.nv.burn:
            atk *= 0.5
        return float(atk)

    def get_defense(self, battle=None) -> float:
        return float(self.defense * self._stage_mult(self.defense_stage))

    def get_spatk(self, battle=None) -> float:
        return float(self.spatk * self._stage_mult(self.spatk_stage))

    def get_spdef(self, battle=None) -> float:
        return float(self.spdef * self._stage_mult(self.spdef_stage))

    def is_alive(self) -> bool:
        return self.hp > 0

    def __repr__(self):
        return f"SimPokemon({self.name} {self.hp}/{self.starting_hp})"


# ═════════════════════════════════════════════════════════════════════════════
# SimTrainer  — mirrors Trainer interface
# ═════════════════════════════════════════════════════════════════════════════
class SimTrainer:
    def __init__(self, name: str, party: list[SimPokemon]):
        self.name           = name
        self.party          = party
        self.current_pokemon = party[0]

        # hazard fields
        self.spikes       = 0
        self.toxic_spikes = 0
        self.stealth_rock = False
        self.sticky_web   = False

    def valid_moves(self, opp_poke):
        """Returns (status, list_of_valid_move_indices)."""
        poke = self.current_pokemon
        if poke is None:
            return "struggle", [0]
        indices = list(range(len(poke.moves)))
        if not indices:
            return "struggle", [0]
        return "normal", indices

    def valid_swaps(self, opp_poke, battle=None, check_trap: bool = True) -> list[int]:
        """Return party indices that can be switched to."""
        cur = self.current_pokemon
        return [i for i, p in enumerate(self.party) if p.is_alive() and p is not cur]

    def has_alive_pokemon(self) -> bool:
        return any(p.is_alive() for p in self.party)


# ═════════════════════════════════════════════════════════════════════════════
# SimBattle  — provides type_effectiveness dict
# ═════════════════════════════════════════════════════════════════════════════
class SimBattle:
    def __init__(self):
        # Pre-compute full table matching real Battle.type_effectiveness format
        self.type_effectiveness: dict[tuple, int] = {}
        for at in ALL_TYPES:
            for dt in ALL_TYPES:
                self.type_effectiveness[(at, dt)] = _eff(at, dt)


# Singleton — reused across all simulated battles
_SIM_BATTLE = SimBattle()


# ═════════════════════════════════════════════════════════════════════════════
# Damage formula  (mirrors gen-8 formula, Lv 50)
# ═════════════════════════════════════════════════════════════════════════════
def _calc_damage(move: SimMove, attacker: SimPokemon, defender: SimPokemon) -> int:
    if move.power == 0:
        return 0
    pw   = move.power
    dc   = move.damage_class
    if dc == SimDC.PHYSICAL:
        a = attacker.get_attack()
        d = defender.get_defense()
    else:
        a = attacker.get_spatk()
        d = defender.get_spdef()

    stab   = 1.5 if move.type in attacker.type_ids else 1.0
    eff    = _matchup(move.type, defender.type_ids)
    crit   = 1.5 if random.randint(1, 24) == 1 else 1.0
    rand   = random.uniform(0.85, 1.0)
    # standard formula
    dmg = ((2 * 50 / 5 + 2) * pw * a / d / 50 + 2) * stab * eff * crit * rand
    return max(1, int(dmg))


# ═════════════════════════════════════════════════════════════════════════════
# Feature encoder  — MUST produce identical 64-element vectors to npc_learning
# ═════════════════════════════════════════════════════════════════════════════
def encode_state(our: SimPokemon, opp: SimPokemon,
                 trainer: SimTrainer, opponent: SimTrainer,
                 battle: SimBattle, turn: int) -> np.ndarray:
    f   = []
    te  = battle.type_effectiveness

    # ── Group 1: our active Pokémon (16) ─────────────────────────────────
    f.append(our.hp / max(1, our.starting_hp))
    f.append(our.attack_stage  / 6)
    f.append(our.defense_stage / 6)
    f.append(our.spatk_stage   / 6)
    f.append(our.spdef_stage   / 6)
    f.append(our.speed_stage   / 6)
    nv = our.nv
    f.append(1.0 if nv.burn     else 0.0)
    f.append(1.0 if nv.paralyze else 0.0)
    f.append(1.0 if (nv.toxic or nv.poison) else 0.0)
    f.append(1.0 if (nv.sleep or nv.freeze) else 0.0)
    spd = our.get_speed();  atk = our.get_attack();  spa = our.get_spatk()
    f.extend([min(spd/300,1), min(atk/300,1), min(spa/300,1)])
    best_pw, best_eff, has_prio = 0.0, 0.5, 0.0
    for m in our.moves:
        pw = m.power or 0
        best_pw = max(best_pw, pw/150)
        if pw > 0:
            eff = _matchup(m.type, opp.type_ids)
            best_eff = max(best_eff, min(eff/4, 1.0))
        if m.priority > 0:
            has_prio = 1.0
    f.extend([min(best_pw,1), best_eff, has_prio])           # total 16

    # ── Group 2: opponent active Pokémon (10) ────────────────────────────
    f.append(opp.hp / max(1, opp.starting_hp))
    onv = opp.nv
    f.append(1.0 if onv.burn     else 0.0)
    f.append(1.0 if onv.paralyze else 0.0)
    f.append(1.0 if (onv.toxic or onv.poison) else 0.0)
    f.append(1.0 if (onv.sleep or onv.freeze) else 0.0)
    o_spd = opp.get_speed();  o_atk = opp.get_attack();  o_spa = opp.get_spatk()
    f.extend([min(o_spd/300,1), min(o_atk/300,1), min(o_spa/300,1)])
    opp_eff, opp_prio = 0.5, 0.0
    for m in opp.moves:
        pw = m.power or 0
        if pw > 0:
            eff = _matchup(m.type, our.type_ids)
            opp_eff = max(opp_eff, min(eff/4,1.0))
        if m.priority > 0:
            opp_prio = 1.0
    f.extend([opp_eff, opp_prio])                            # total 26

    # ── Group 3: our 4 moves (4×4 = 16) ─────────────────────────────────
    for i in range(4):
        if i < len(our.moves):
            m   = our.moves[i]
            pw  = m.power or 0
            eff = _matchup(m.type, opp.type_ids) if pw > 0 else 1.0
            acc = (m.accuracy or 100) / 100
            pri = 1.0 if m.priority > 0 else 0.0
            f.extend([min(pw/150,1), min(eff/4,1), acc, pri])
        else:
            f.extend([0.0, 0.0, 0.0, 0.0])                  # total 42

    # ── Group 4: switch options (6) ───────────────────────────────────────
    valid_sw   = trainer.valid_swaps(opp)
    can_sw     = 1.0 if valid_sw else 0.0
    n_sw       = len(valid_sw) / 5.0
    best_sw_hp, best_sw_eff, best_sw_spd = 0.0, 0.5, 0.0
    bench_hps  = []
    for pi in valid_sw:
        cand = trainer.party[pi]
        hp_r = cand.hp / max(1, cand.starting_hp)
        best_sw_hp = max(best_sw_hp, hp_r)
        bench_hps.append(hp_r)
        if cand.get_raw_speed() > o_spd:
            best_sw_spd = 1.0
        for m in cand.moves:
            pw = m.power or 0
            if pw > 0:
                eff = _matchup(m.type, opp.type_ids)
                best_sw_eff = max(best_sw_eff, min(eff/4,1.0))
    avg_bench  = float(np.mean(bench_hps)) if bench_hps else 0.5
    f.extend([best_sw_hp, best_sw_eff, n_sw, can_sw, avg_bench, best_sw_spd])  # total 48

    # ── Group 5: field (12) ───────────────────────────────────────────────
    tr, op = trainer, opponent
    alive_tr = sum(1 for p in tr.party if p.is_alive())
    alive_op = sum(1 for p in op.party if p.is_alive())
    avg_hp_tr = np.mean([p.hp/max(1,p.starting_hp) for p in tr.party if p.is_alive()]) if alive_tr else 0
    avg_hp_op = np.mean([p.hp/max(1,p.starting_hp) for p in op.party if p.is_alive()]) if alive_op else 0
    f.extend([
        tr.spikes/3, tr.toxic_spikes/2,
        1.0 if tr.stealth_rock else 0.0, 1.0 if tr.sticky_web else 0.0,
        op.spikes/3, op.toxic_spikes/2,
        1.0 if op.stealth_rock else 0.0, 1.0 if op.sticky_web else 0.0,
        alive_tr/6, alive_op/6, avg_hp_tr, avg_hp_op,
    ])                                                       # total 60

    # ── Group 6: global (4) ───────────────────────────────────────────────
    our_tot = sum(p.hp for p in tr.party)
    opp_tot = sum(p.hp for p in op.party)
    momentum = our_tot / max(1, our_tot + opp_tot)
    f.extend([
        min(turn/50, 1.0),
        1.0 if spd > o_spd else (0.5 if spd == o_spd else 0.0),
        momentum,
        (alive_tr - alive_op + 6) / 12,
    ])                                                       # total 64

    arr = np.array(f, dtype=np.float32)
    assert len(arr) == N_FEATURES, f"SimEncoder bug: {len(arr)} != {N_FEATURES}"
    return arr


# ═════════════════════════════════════════════════════════════════════════════
# Heuristic AI for the simulator  (opponent the DQN trains against)
# ═════════════════════════════════════════════════════════════════════════════
def _heuristic_move(trainer: SimTrainer, opponent: SimTrainer) -> tuple[int, int | None]:
    """
    Returns (move_idx, switch_party_idx_or_None).
    Mirrors the old npc_ai heuristic — type-matchup aware, switches when threatened.
    """
    poke = trainer.current_pokemon
    opp  = opponent.current_pokemon
    if poke is None or opp is None:
        return 0, None

    _, move_indices = trainer.valid_moves(opp)
    valid_sw        = trainer.valid_swaps(opp)

    # score moves
    best_mi, best_score = move_indices[0], -999.0
    for mi in move_indices:
        m  = poke.moves[mi]
        pw = m.power or 0
        if pw == 0:
            score = 8.0
        else:
            eff   = _matchup(m.type, opp.type_ids)
            stab  = 1.5 if m.type in poke.type_ids else 1.0
            score = pw * eff * stab / 100
            if eff == 0:
                score = -50
        if m.priority > 0 and poke.get_speed() < opp.get_speed():
            score += 15
        if score > best_score:
            best_score = score;  best_mi = mi

    # consider switch if in danger
    if valid_sw and random.random() < 0.15:
        best_sw, best_sw_score = None, -999.0
        for pi in valid_sw:
            cand = trainer.party[pi]
            sw_score = cand.hp / max(1, cand.starting_hp) * 50
            for m in cand.moves:
                pw = m.power or 0
                if pw > 0:
                    eff = _matchup(m.type, opp.type_ids)
                    if eff >= 2:
                        sw_score += 20
            if sw_score > best_sw_score:
                best_sw_score = sw_score;  best_sw = pi
        if best_sw is not None and best_sw_score > 60:
            return best_mi, best_sw

    return best_mi, None


# ═════════════════════════════════════════════════════════════════════════════
# Simulated battle runner
# ═════════════════════════════════════════════════════════════════════════════
def _gen_team(name: str, size: int = 6) -> SimTrainer:
    """Generate a competitive random team."""
    pool  = random.sample(_ARCHETYPES, min(size, len(_ARCHETYPES)))
    party = []
    for (pname, type_ids, base) in pool:
        moves = _rand_moves(type_ids)
        party.append(SimPokemon(pname, type_ids, base, moves))
    return SimTrainer(name, party)


def _apply_status_end_turn(poke: SimPokemon):
    """End-of-turn status damage."""
    if poke.nv.burn and poke.hp > 0:
        poke.hp = max(0, poke.hp - max(1, poke.starting_hp // 16))
    if (poke.nv.toxic or poke.nv.poison) and poke.hp > 0:
        poke.nv.toxic_count += 1
        dmg = max(1, poke.starting_hp * poke.nv.toxic_count // 16)
        poke.hp = max(0, poke.hp - dmg)


def run_one_battle(
    q_net: DQNetwork,
    tgt_net: DQNetwork,
    buf: ReplayBuffer,
    epsilon: float,
    verbose: bool = False,
) -> bool:
    """
    Run one simulated battle.  The DQN plays trainer1; a heuristic plays trainer2.
    Pushes transitions into buf and returns True if DQN won.
    """
    battle   = _SIM_BATTLE
    trainer1 = _gen_team("DQN")
    trainer2 = _gen_team("Heuristic")
    turn     = 0

    pending_s = None
    pending_a = None
    prev_our_hp    = sum(p.hp for p in trainer1.party)
    prev_opp_hp    = sum(p.hp for p in trainer2.party)
    prev_our_alive = len([p for p in trainer1.party if p.is_alive()])
    prev_opp_alive = len([p for p in trainer2.party if p.is_alive()])

    def _get_dqn_action(our: SimPokemon, opp: SimPokemon) -> tuple[int, int | None]:
        state    = encode_state(our, opp, trainer1, trainer2, battle, turn)
        _, m_idx = trainer1.valid_moves(opp)
        sw_idx   = trainer1.valid_swaps(opp)
        # build mask
        mask = np.zeros(N_ACTIONS, dtype=bool)
        for mi in m_idx:
            if mi < 4: mask[mi] = True
        for pi in sw_idx:
            if pi < 5: mask[4+pi] = True
        if not mask.any(): mask[:] = True

        if random.random() < epsilon:
            valid = np.where(mask)[0]
            action = int(np.random.choice(valid))
        else:
            q        = q_net.predict(state)
            q_masked = q.copy(); q_masked[~mask] = -1e9
            action   = int(np.argmax(q_masked))
        return state, action, m_idx, sw_idx

    MAX_TURNS = 80
    winner    = None   # "dqn" or "heuristic"

    while turn < MAX_TURNS:
        our = trainer1.current_pokemon
        opp = trainer2.current_pokemon

        # ── DQN decision ─────────────────────────────────────────────────
        state, action, m_idx, sw_idx = _get_dqn_action(our, opp)

        # store transition from previous turn
        if pending_s is not None:
            cur_our_hp    = sum(p.hp for p in trainer1.party)
            cur_opp_hp    = sum(p.hp for p in trainer2.party)
            cur_our_alive = sum(1 for p in trainer1.party if p.is_alive())
            cur_opp_alive = sum(1 for p in trainer2.party if p.is_alive())
            our_max = sum(p.starting_hp for p in trainer1.party) or 1
            opp_max = sum(p.starting_hp for p in trainer2.party) or 1
            r  = (max(0,prev_opp_hp-cur_opp_hp)/opp_max - max(0,prev_our_hp-cur_our_hp)/our_max) * 0.3
            r += max(0, prev_opp_alive - cur_opp_alive) * 0.25
            r -= max(0, prev_our_alive - cur_our_alive) * 0.25
            r  = float(np.clip(r, -1, 1))
            buf.push(pending_s, pending_a, r, state, False)
            prev_our_hp    = cur_our_hp;    prev_opp_hp    = cur_opp_hp
            prev_our_alive = cur_our_alive; prev_opp_alive = cur_opp_alive

        pending_s = state;  pending_a = action

        # ── Heuristic decision ────────────────────────────────────────────
        h_mi, h_sw = _heuristic_move(trainer2, trainer1)

        # ── Execute actions ───────────────────────────────────────────────
        # DQN action
        dqn_sw = None
        if action >= 4:
            pi = action - 4
            if pi not in sw_idx and sw_idx: pi = sw_idx[0]
            if pi < len(trainer1.party) and trainer1.party[pi].is_alive():
                trainer1.current_pokemon = trainer1.party[pi]
                dqn_sw = pi

        # Heuristic switch
        if h_sw is not None and h_sw < len(trainer2.party) and trainer2.party[h_sw].is_alive():
            trainer2.current_pokemon = trainer2.party[h_sw]

        # Speed order for moves
        our  = trainer1.current_pokemon
        opp  = trainer2.current_pokemon
        t1_first = our.get_speed() > opp.get_speed()

        def _exec_move(attacker: SimPokemon, defender: SimPokemon,
                       tr_att: SimTrainer, tr_def: SimTrainer,
                       move_idx: int, is_dqn: bool) -> bool:
            """Execute one move. Returns True if battle ended."""
            m  = attacker.moves[move_idx]
            pw = m.power or 0

            # miss
            if m.accuracy and random.randint(1, 100) > m.accuracy:
                return False

            if pw > 0:
                dmg = _calc_damage(m, attacker, defender)
                defender.hp = max(0, defender.hp - dmg)
            elif m.effect:
                _apply_status_effect(m.effect, attacker, defender, tr_att, tr_def)
            return False

        def _apply_status_effect(eff: str,
                                 att: SimPokemon, dfd: SimPokemon,
                                 tr_a: SimTrainer, tr_d: SimTrainer):
            if eff == "burn":
                dfd.nv.apply("burn")
            elif eff == "paralyze":
                dfd.nv.apply("paralyze")
            elif eff == "toxic":
                dfd.nv.apply("toxic")
            elif eff == "heal":
                att.hp = min(att.starting_hp, att.hp + att.starting_hp // 2)
            elif eff == "stealth_rock":
                if not tr_d.stealth_rock:
                    tr_d.stealth_rock = True
            elif eff == "spikes" and tr_d.spikes < 3:
                tr_d.spikes += 1
            elif eff == "toxic_spikes" and tr_d.toxic_spikes < 2:
                tr_d.toxic_spikes += 1
            elif eff == "atk+2":
                att.attack_stage = min(6, att.attack_stage + 2)
            elif eff == "spatk+1":
                att.spatk_stage = min(6, att.spatk_stage + 1)
            elif eff == "spatk+2":
                att.spatk_stage = min(6, att.spatk_stage + 2)
            elif eff == "defog":
                tr_d.stealth_rock = False; tr_d.spikes = 0; tr_d.toxic_spikes = 0
                tr_a.stealth_rock = False; tr_a.spikes = 0; tr_a.toxic_spikes = 0

        # Execute in speed order
        if dqn_sw is None:
            dqn_move_idx = action if action in m_idx else m_idx[0]
        if t1_first:
            if dqn_sw is None:
                _exec_move(our, opp, trainer1, trainer2, dqn_move_idx, True)
            if opp.is_alive() and h_sw is None:
                _exec_move(opp, our, trainer2, trainer1, h_mi, False)
        else:
            if h_sw is None:
                _exec_move(opp, our, trainer2, trainer1, h_mi, False)
            if our.is_alive() and dqn_sw is None:
                _exec_move(our, opp, trainer1, trainer2, dqn_move_idx, True)

        # End of turn status
        _apply_status_end_turn(our)
        _apply_status_end_turn(opp)

        # Faint checks
        if not opp.is_alive():
            sw_list = trainer2.valid_swaps(our)
            if sw_list:
                trainer2.current_pokemon = trainer2.party[sw_list[0]]
            else:
                winner = "dqn";  break
        if not our.is_alive():
            sw_list = trainer1.valid_swaps(opp)
            if sw_list:
                trainer1.current_pokemon = trainer1.party[sw_list[0]]
            else:
                winner = "heuristic";  break

        if not trainer2.has_alive_pokemon():
            winner = "dqn";    break
        if not trainer1.has_alive_pokemon():
            winner = "heuristic"; break

        turn += 1

    # ── Terminal transition ───────────────────────────────────────────────
    dqn_won   = (winner == "dqn")
    terminal_r = 1.0 if dqn_won else -1.0
    if pending_s is not None:
        terminal_ns = encode_state(
            trainer1.current_pokemon, trainer2.current_pokemon,
            trainer1, trainer2, battle, turn,
        ) if trainer1.current_pokemon and trainer2.current_pokemon else pending_s
        buf.push(pending_s, pending_a, terminal_r, terminal_ns, True)

    return dqn_won


# ═════════════════════════════════════════════════════════════════════════════
# Pre-training engine
# ═════════════════════════════════════════════════════════════════════════════
class Pretrainer:
    def __init__(self):
        self.q_net   = DQNetwork()
        self.tgt_net = DQNetwork()
        self.buf     = ReplayBuffer()
        self.epsilon = EPS_START
        self.battles  = 0
        self.wins     = 0
        self.losses: list[float] = []
        self._load()

    def _load(self):
        if os.path.exists(Q_NET_PATH):
            try:
                self.q_net  = DQNetwork.load(Q_NET_PATH)
                self.tgt_net = (DQNetwork.load(TGT_NET_PATH)
                                if os.path.exists(TGT_NET_PATH) else DQNetwork())
                if not os.path.exists(TGT_NET_PATH):
                    self.tgt_net.copy_weights_from(self.q_net)
                print(f"  ✅ Loaded existing model (Adam t={self.q_net.t:,})")
            except Exception as e:
                print(f"  ⚠️ Load error ({e}) — starting fresh")
        else:
            self.tgt_net.copy_weights_from(self.q_net)
            print("  🆕 No existing model — starting from scratch")
        self.buf.load(BUFFER_PATH)

        # Restore epsilon from stats if available
        if os.path.exists(STATS_PATH):
            try:
                import json
                with open(STATS_PATH) as f:
                    d = json.load(f)
                self.battles = d.get("battles", 0)
                self.wins    = d.get("wins",    0)
                saved_eps    = d.get("epsilon", EPS_START)
                # If already at floor, re-open exploration so sim training is useful
                if saved_eps <= EPS_END + 1e-4:
                    self.epsilon = 0.30
                    print(f"  ⚡  Epsilon was at floor — reset to {self.epsilon:.2f}")
                else:
                    self.epsilon = max(EPS_END, saved_eps)
                print(f"  📊 Resuming from battle {self.battles}, ε={self.epsilon:.4f}")
            except Exception:
                pass

    def _save(self):
        import json
        self.q_net.save(Q_NET_PATH)
        self.tgt_net.save(TGT_NET_PATH)
        self.buf.save(BUFFER_PATH)
        avg_l = float(np.mean(self.losses[-1000:])) if self.losses else 0.0
        wr    = self.wins / max(1, self.battles)
        with open(STATS_PATH, "w") as f:
            json.dump({
                "battles":     self.battles,
                "wins":        self.wins,
                "epsilon":     self.epsilon,
                "train_steps": self.q_net.t,
                "avg_loss":    avg_l,
                "total_loss":  sum(self.losses),
                "buffer_size": len(self.buf),
            }, f, indent=2)

    def _train(self) -> float:
        if len(self.buf) < MIN_BUF:
            return 0.0
        s, a, r, ns, d = self.buf.sample(BATCH_SZ)
        nq_main  = self.q_net.predict(ns)
        nq_tgt   = self.tgt_net.predict(ns)
        best_a   = np.argmax(nq_main, axis=1)
        next_val = nq_tgt[np.arange(len(s)), best_a]
        targets  = r + GAMMA * next_val * (1 - d)
        return self.q_net.train_batch(s, targets, a)

    def run(self, n_battles: int = 2000, verbose: bool = False):
        print(f"\n{'═'*60}")
        print(f"  🏋️  Pre-training: {n_battles} simulated battles")
        print(f"  Buffer start: {len(self.buf):,}  |  ε = {self.epsilon:.4f}")
        print(f"{'═'*60}")

        t0        = time.time()
        win_streak= []

        for i in range(n_battles):
            won = run_one_battle(self.q_net, self.tgt_net,
                                 self.buf, self.epsilon, verbose)
            self.battles += 1
            if won: self.wins += 1
            win_streak.append(int(won))

            # train after every battle — use same schedule as live battles
            if len(self.buf) >= MIN_BUF:
                for _ in range(STEPS_PER_END):
                    loss = self._train()
                    self.losses.append(loss)

            # update target network
            if self.battles % TGT_UPDATE == 0:
                self.tgt_net.copy_weights_from(self.q_net)

            # decay epsilon
            self.epsilon = max(EPS_END, self.epsilon * EPS_DECAY)

            # progress display every 50 battles
            if (i + 1) % 50 == 0:
                wr    = np.mean(win_streak[-100:]) if win_streak else 0
                avg_l = float(np.mean(self.losses[-200:])) if self.losses else 0
                elapsed = time.time() - t0
                bps     = (i+1) / elapsed
                eta_s   = (n_battles - i - 1) / max(bps, 0.01)
                eta_m   = int(eta_s // 60)
                bar_w   = 30
                done    = int((i+1)/n_battles * bar_w)
                bar     = "█"*done + "░"*(bar_w-done)
                print(f"  [{bar}] {i+1}/{n_battles}  "
                      f"wr={wr:.0%}  ε={self.epsilon:.3f}  "
                      f"loss={avg_l:.4f}  buf={len(self.buf):,}  "
                      f"ETA {eta_m}m")

            # save checkpoint
            if self.battles % (SAVE_FREQ * 5) == 0:
                self._save()

        self._save()
        elapsed = time.time() - t0
        total_wr = self.wins / max(1, self.battles)
        print(f"\n{'═'*60}")
        print(f"  ✅ Pre-training complete in {elapsed:.0f}s")
        print(f"  Total battles: {self.battles:,}  |  Win rate: {total_wr:.1%}")
        print(f"  Buffer size:   {len(self.buf):,}")
        print(f"  Model saved → {Q_NET_PATH}")
        print(f"{'═'*60}")
        show_progress()


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-train the NPC DQN AI")
    parser.add_argument("--battles", type=int, default=2000,
                        help="Number of simulated battles to run (default: 2000)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show per-battle debug output")
    args = parser.parse_args()

    print("═" * 60)
    print("  🤖 NPC DQN — Simulated Pre-Training")
    print("  Trains the AI against a heuristic opponent before real play.")
    print("  Recommended: 2000+ battles. More = stronger starting point.")
    print("═" * 60)

    pt = Pretrainer()
    pt.run(n_battles=args.battles, verbose=args.verbose)
