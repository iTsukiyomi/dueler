"""
ai/evaluation.py — Arena matches + ELO tracking.

Used in two places:

* During training, after every ``OPT_EVAL_EVERY`` steps we play
  ``EVAL_MATCHES`` headless games between the latest network and the best
  network so far. If the candidate's win rate ≥ ``EVAL_PROMOTE_WR`` we
  promote it.

* On demand from the Discord bot (``;duel npcaistats``) to print the
  current ELO trajectory.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

<<<<<<< HEAD
=======
import signal
>>>>>>> 05d15f7 (updated npc ai)
import numpy as np

from . import config as C
from .action_mask import legal_action_mask, apply_action
from .encoder import BattleEncoder
from .hidden_info import HiddenInfoTracker
from .mcts import MCTS
from .simulator import HeadlessBattle, initial_send_out, run_turn
from .team_loader import random_two_teams
from ..trainers.npc_trainer import NPCTrainer


# ─────────────────────────────────────────────────────────────────────────────
# ELO bookkeeping
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class EloState:
    ratings: dict = field(default_factory=dict)
    history: list = field(default_factory=list)         # list of (step, name, rating)

    def get(self, name: str) -> float:
        return float(self.ratings.get(name, C.ELO_INIT))

    def record_match(self, a: str, b: str, score_a: float, *, k: float = C.ELO_K) -> None:
        ra = self.get(a)
        rb = self.get(b)
        ea = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
        eb = 1.0 - ea
        score_b = 1.0 - score_a
        self.ratings[a] = ra + k * (score_a - ea)
        self.ratings[b] = rb + k * (score_b - eb)

    def append_history(self, step: int) -> None:
        for n, r in self.ratings.items():
            self.history.append((step, n, r))

    @classmethod
    def load(cls, path: str | Path) -> "EloState":
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        st = cls(
            ratings={k: float(v) for k, v in data.get("ratings", {}).items()},
            history=[tuple(x) for x in data.get("history", [])],
        )
        return st

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"ratings": self.ratings, "history": self.history}, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Single deterministic match — both sides use *real* inference engines
# ─────────────────────────────────────────────────────────────────────────────
def play_match(inference_a, inference_b,
               *,
               simulations: int = C.MCTS_EVAL_SIMS,
               seed: Optional[int] = None,
               max_turns: int = C.SELFPLAY_MAX_TURNS
               ) -> int:
    """Play one match. Returns ``1`` if A wins, ``-1`` if B wins, ``0`` draw."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed & 0xFFFFFFFF)

    party1, party2 = random_two_teams(seed=seed)
    t1 = NPCTrainer("A", party1)
    t2 = NPCTrainer("B", party2)
    battle = HeadlessBattle(t1, t2)
    initial_send_out(battle)

    encA = BattleEncoder(HiddenInfoTracker())
    encB = BattleEncoder(HiddenInfoTracker())
    mctsA = MCTS(inference_a, simulations=simulations, encoder=encA, add_root_noise=False)
    mctsB = MCTS(inference_b, simulations=simulations, encoder=encB, add_root_noise=False)

    for _ in range(max_turns):
        if t1.current_pokemon is None and t1.has_alive_pokemon():
            _forced_swap(t1, t2, battle, mctsA, side=1)
        if t2.current_pokemon is None and t2.has_alive_pokemon():
            _forced_swap(t2, t1, battle, mctsB, side=2)

        if not t1.has_alive_pokemon():
            return -1
        if not t2.has_alive_pokemon():
            return  1

        _, a1 = mctsA.search(battle, our_side=1, temperature=0.0)
        apply_action(a1, t1, t2, battle)
        _, a2 = mctsB.search(battle, our_side=2, temperature=0.0)
        apply_action(a2, t2, t1, battle)

        _msg, w = run_turn(battle)
        if w is t1:
            return  1
        if w is t2:
            return -1

    h1 = sum(max(0, p.hp) for p in t1.party)
    h2 = sum(max(0, p.hp) for p in t2.party)
    if h1 > h2: return  1
    if h2 > h1: return -1
    return 0


def _forced_swap(trainer, opponent, battle, mcts, side: int) -> None:
    _, act = mcts.search(battle, our_side=side, temperature=0.0)
    apply_action(act, trainer, opponent, battle)
    if isinstance(trainer.selected_action, int):
        slot = trainer.selected_action
        target = trainer.party[slot] if 0 <= slot < len(trainer.party) else None
        if target is None or getattr(target, "hp", 0) <= 0:
            slot = next((i for i, p in enumerate(trainer.party) if p.hp > 0), None)
        if slot is not None:
            try:
                trainer.switch_poke(slot)
                if opponent.current_pokemon is not None:
                    battle.msg += trainer.current_pokemon.send_out(opponent.current_pokemon, battle)
            except Exception:
                pass
        trainer.selected_action = None


# ─────────────────────────────────────────────────────────────────────────────
# Tournament between candidate and best
# ─────────────────────────────────────────────────────────────────────────────
def evaluate(candidate_inference, best_inference,
             *,
             n_matches: int = C.EVAL_MATCHES,
             simulations: int = C.MCTS_EVAL_SIMS,
             seed: Optional[int] = None
             ) -> Tuple[float, int, int, int]:
    """Return ``(win_rate, wins, losses, draws)`` for the candidate."""
    wins = losses = draws = 0
    rng = random.Random(seed)
<<<<<<< HEAD
=======
    def _guarded_match(*a, **kw):
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError()))
        signal.alarm(180)
        try:
            return play_match(*a, **kw)
        except TimeoutError:
            return 0
        finally:
            signal.alarm(0)

>>>>>>> 05d15f7 (updated npc ai)
    for i in range(n_matches):
        s = rng.randint(0, 2**31 - 1)
        # alternate sides to remove first-move advantage
        if i % 2 == 0:
<<<<<<< HEAD
            r = play_match(candidate_inference, best_inference,
=======
            r = _guarded_match(candidate_inference, best_inference,
>>>>>>> 05d15f7 (updated npc ai)
                           simulations=simulations, seed=s)
            if r == 1:
                wins += 1
            elif r == -1:
                losses += 1
            else:
                draws += 1
        else:
<<<<<<< HEAD
            r = play_match(best_inference, candidate_inference,
=======
            r = _guarded_match(best_inference, candidate_inference,
>>>>>>> 05d15f7 (updated npc ai)
                           simulations=simulations, seed=s)
            if r == 1:
                losses += 1
            elif r == -1:
                wins += 1
            else:
                draws += 1
    total = max(1, n_matches)
    return wins / total, wins, losses, draws


__all__ = ["EloState", "play_match", "evaluate"]
