"""
ai/heuristic.py — Fast, zero-dependency heuristic policy.

Used when poke_engine is unavailable or when inference times out.
No imports from torch / numpy / poke_engine — must stay lightweight.

Priority order (mirrors ml-duel-auditor fallback spec):
  1. Pick any move that OHKOs the opponent.
  2. Switch if active HP < 25 % and a type-resistant switch exists.
  3. Pick the legal damaging move with highest expected damage.
  4. Tiebreak: accuracy → priority bracket → deterministic index.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..trainers.trainer_base import Trainer
    from ..battle.battle import Battle
    from ..pokemon import DuelPokemon

log = logging.getLogger("dueler.ai.heuristic")

# ─── Type chart (18×18, normal→fairy, index by ElementType int - 1) ─────────
# Rows = attacker type, Cols = defender type.
# ElementType: 1=Normal, 2=Fighting, 3=Flying, 4=Poison, 5=Ground, 6=Rock,
#              7=Bug, 8=Ghost, 9=Steel, 10=Fire, 11=Water, 12=Grass,
#              13=Electric, 14=Psychic, 15=Ice, 16=Dragon, 17=Dark, 18=Fairy
_TC: list[list[float]] = [
    # NOR FGT FLY POI GRD ROC BUG GHO STL FIR WAT GRA ELE PSY ICE DRG DRK FAI
    [1,   1,   1,   1,   1,   0.5, 1,   0,   0.5, 1,   1,   1,   1,   1,   1,   1,   1,   1  ],  # NOR
    [2,   1,   0.5, 0.5, 1,   2,   0.5, 0,   2,   1,   1,   1,   1,   0.5, 2,   1,   2,   0.5],  # FGT
    [1,   2,   1,   1,   1,   0.5, 2,   1,   0.5, 1,   1,   2,   0.5, 1,   1,   1,   1,   1  ],  # FLY
    [1,   1,   1,   0.5, 0.5, 0.5, 1,   0.5, 0,   1,   1,   2,   1,   1,   1,   1,   1,   2  ],  # POI
    [1,   1,   0,   2,   1,   2,   0.5, 1,   2,   2,   1,   0.5, 2,   1,   1,   1,   1,   1  ],  # GRD
    [1,   0.5, 2,   1,   0.5, 1,   2,   1,   0.5, 2,   1,   1,   1,   1,   2,   1,   1,   1  ],  # ROC
    [1,   0.5, 0.5, 0.5, 1,   1,   1,   0.5, 0.5, 0.5, 1,   2,   1,   2,   1,   1,   2,   0.5],  # BUG
    [0,   1,   1,   1,   1,   1,   1,   2,   1,   1,   1,   1,   1,   2,   1,   1,   0.5, 1  ],  # GHO
    [1,   1,   1,   1,   1,   2,   1,   1,   0.5, 0.5, 0.5, 1,   0.5, 1,   2,   1,   1,   2  ],  # STL
    [1,   1,   1,   1,   1,   0.5, 2,   1,   2,   0.5, 0.5, 2,   1,   1,   2,   0.5, 1,   1  ],  # FIR
    [1,   1,   1,   1,   2,   2,   1,   1,   1,   2,   0.5, 0.5, 1,   1,   1,   0.5, 1,   1  ],  # WAT
    [1,   1,   0.5, 0.5, 2,   2,   0.5, 1,   0.5, 0.5, 2,   0.5, 1,   1,   1,   0.5, 1,   1  ],  # GRA
    [1,   1,   2,   1,   0,   1,   1,   1,   1,   1,   2,   0.5, 0.5, 1,   1,   0.5, 1,   1  ],  # ELE
    [1,   2,   1,   2,   1,   1,   1,   1,   0.5, 1,   1,   1,   1,   0.5, 1,   1,   0,   1  ],  # PSY
    [1,   1,   2,   1,   2,   1,   1,   1,   0.5, 0.5, 0.5, 2,   1,   1,   0.5, 2,   1,   1  ],  # ICE
    [1,   1,   1,   1,   1,   1,   1,   1,   0.5, 1,   1,   1,   1,   1,   1,   2,   1,   0  ],  # DRG
    [1,   0.5, 1,   1,   1,   1,   1,   2,   1,   1,   1,   1,   1,   2,   1,   1,   0.5, 0.5],  # DRK
    [1,   2,   1,   0.5, 1,   1,   1,   1,   0.5, 0.5, 1,   1,   1,   1,   1,   2,   2,   1  ],  # FAI
]


def _type_effectiveness(atk_type_id: int, def_type_ids: list[int]) -> float:
    """Return the overall type effectiveness multiplier."""
    row = atk_type_id - 1
    if row < 0 or row >= 18:
        return 1.0
    mult = 1.0
    for d in def_type_ids:
        col = d - 1
        if 0 <= col < 18:
            mult *= _TC[row][col]
    return mult


def _estimate_damage(move, attacker: "DuelPokemon", defender: "DuelPokemon") -> float:
    """
    Very rough damage estimate — enough to rank moves, not a precise roll.
    Ignores items, abilities, weather, terrain, crits, random roll.
    """
    from ..enums import DamageClass

    power = move.power or 0
    if power <= 0:
        return 0.0

    dc = move.damage_class
    if dc == DamageClass.PHYSICAL:
        atk = attacker.get_raw_attack()
        def_ = defender.get_raw_defense()
    elif dc == DamageClass.SPECIAL:
        atk = attacker.get_raw_spatk()
        def_ = defender.get_raw_spdef()
    else:
        return 0.0

    if def_ == 0:
        return float("inf")

    base = ((2 * attacker.level / 5 + 2) * power * atk / def_) / 50 + 2

    # STAB
    move_type = move.type  # ElementType int
    if move_type in attacker.type_ids:
        base *= 1.5

    # Type effectiveness
    base *= _type_effectiveness(int(move_type), [int(t) for t in defender.type_ids])

    return base


def _type_resist_score(poke: "DuelPokemon", opp: "DuelPokemon") -> float:
    """
    Returns the sum of type effectiveness for the opponent's primary type
    against this pokemon (lower = better resist).
    """
    score = 0.0
    for opp_t in opp.type_ids:
        score += _type_effectiveness(int(opp_t), [int(t) for t in poke.type_ids])
    return score


# ─────────────────────────────────────────────────────────────────────────────

def heuristic_choose_move(
    trainer: "Trainer",
    opponent_poke: "DuelPokemon | None",
    battle: "Battle",
) -> tuple:
    """
    Return ``(move_or_struggle, switch_idx_or_None)`` — the same contract
    as ``NPCTeamAI.choose_move()``.
    """
    from ..moves import Move

    current = trainer.current_pokemon
    if current is None:
        return Move.struggle(), None

    # ── Gather legal moves ───────────────────────────────────────────────────
    status_code, movedata = trainer.valid_moves(opponent_poke)
    if status_code == "forced":
        return movedata, None
    if status_code == "struggle":
        return Move.struggle(), None

    # ── Score each move ──────────────────────────────────────────────────────
    scored: list[tuple[float, int, object]] = []
    for idx in movedata:
        move = current.moves[idx]
        dmg = _estimate_damage(move, current, opponent_poke) if opponent_poke else 0.0
        acc = move.accuracy if move.accuracy else 100
        pri = move.priority if move.priority else 0
        scored.append((dmg, acc, pri, idx, move))

    if not scored:
        return Move.struggle(), None

    scored.sort(key=lambda x: (x[0], x[1], x[2], -x[3]), reverse=True)

    # ── OHKO check — always prefer a kill ───────────────────────────────────
    if opponent_poke and opponent_poke.hp > 0:
        best_dmg, _, _, _, best_move = scored[0]
        if best_dmg >= opponent_poke.hp:
            return best_move, None

    # ── Low-HP switch consideration ──────────────────────────────────────────
    if current.hp < current.starting_hp * 0.25 and opponent_poke is not None:
        valid_swaps = trainer.valid_swaps(opponent_poke, battle, check_trap=True)
        if valid_swaps:
            best_swap_idx = _best_switch(valid_swaps, trainer, opponent_poke)
            if best_swap_idx is not None:
                return Move.struggle(), best_swap_idx

    # ── Highest damage move ──────────────────────────────────────────────────
    _, _, _, _, best_move = scored[0]
    return best_move, None


def heuristic_choose_switch(
    trainer: "Trainer",
    opponent_poke: "DuelPokemon | None",
    battle: "Battle",
) -> int:
    """Return the party index of the best replacement pokemon."""
    valid_swaps = trainer.valid_swaps(
        opponent_poke, battle, check_trap=False
    )
    if not valid_swaps:
        # Emergency: any alive pokemon
        for i, p in enumerate(trainer.party):
            if p.hp > 0 and p is not trainer.current_pokemon:
                return i
        return 0

    best = _best_switch(valid_swaps, trainer, opponent_poke)
    return best if best is not None else valid_swaps[0]


def _best_switch(
    valid_swaps: list[int],
    trainer: "Trainer",
    opponent_poke: "DuelPokemon | None",
) -> int | None:
    """
    Pick the bench slot with the best type resistance vs. the opponent.
    Lowest resist_score = best match-up.
    """
    if not valid_swaps or opponent_poke is None:
        return valid_swaps[0] if valid_swaps else None

    best_idx = valid_swaps[0]
    best_score = float("inf")
    for idx in valid_swaps:
        poke = trainer.party[idx]
        if poke.hp <= 0:
            continue
        score = _type_resist_score(poke, opponent_poke)
        if score < best_score:
            best_score = score
            best_idx = idx
    return best_idx
