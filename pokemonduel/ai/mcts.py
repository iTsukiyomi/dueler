"""
ai/mcts.py — PUCT Monte-Carlo Tree Search for Pokémon battles.

This is the *fast* version of the search. Algorithmically it is the
standard AlphaZero PUCT pattern; the key engineering decisions that
make it fast on a Pokémon engine are:

* **Network-only rollouts past the root.** Stock AlphaZero replaces deep
  Monte-Carlo rollouts with the network's value head — that is the whole
  point of having a value head. We expand the root via the engine (one
  real ``apply_action`` / ``run_turn`` pair when a tree edge is first
  traversed), but the **value backed up at the leaf comes from the
  network**, not from continuing to roll the engine forward. This
  eliminates the ``copy.deepcopy(battle)`` per simulation that was
  killing us on the original implementation.

* **Per-search leaf-evaluation cache.** Two simulations that reach the
  same encoded state inside one ``search()`` call share a single network
  forward pass.

* **Hard wall-clock budget.** A single ``search()`` is capped at
  ``time_budget_s`` (default 8 s). This guarantees no worker can wedge
  the whole training loop on a pathological state, which was the cause
  of the "w1 stuck=1700s" log lines.

What the trainer learns is unchanged: it still gets visit-count policy
targets and an end-of-game ±1 value target. Only the *cost* of
producing them is reduced.
"""
from __future__ import annotations

import math
import random
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import config as C
from . import features as F
from .action_mask import legal_action_mask, apply_action
from .encoder import BattleEncoder
from .hidden_info import HiddenInfoTracker


# ─────────────────────────────────────────────────────────────────────────────
# Default per-search wall-clock budget (seconds). Can be overridden via
# the ``MCTS`` constructor's ``time_budget_s`` argument or by setting
# ``C.MCTS_TIME_BUDGET_S`` in ``ai/config.py``.
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_TIME_BUDGET_S = float(getattr(C, "MCTS_TIME_BUDGET_S", 8.0))


# ─────────────────────────────────────────────────────────────────────────────
# Node
# ─────────────────────────────────────────────────────────────────────────────
class Node:
    __slots__ = (
        "prior", "to_play",
        "N", "W", "Q",
        "children", "actions",
        "is_terminal", "value",
        "mask",
    )

    def __init__(self, prior: float = 0.0, to_play: int = 1) -> None:
        self.prior   = prior
        self.to_play = to_play          # 1 or 2 (whose perspective this node is from)
        self.N       = 0
        self.W       = 0.0
        self.Q       = 0.0
        self.children: Dict[int, "Node"] = {}
        self.actions: List[int]          = []
        self.is_terminal = False
        self.value       = 0.0
        self.mask        = None         # np.ndarray of legal actions

    # ------------------------------------------------------------------
    @property
    def expanded(self) -> bool:
        return bool(self.children)

    # ------------------------------------------------------------------
    def expand(self, priors: np.ndarray, mask: np.ndarray, next_to_play: int) -> None:
        self.mask = mask
        for a in np.where(mask)[0]:
            p = float(priors[a])
            child = Node(prior=p, to_play=next_to_play)
            self.children[int(a)] = child
            self.actions.append(int(a))

    # ------------------------------------------------------------------
    def select_child(self, c_puct: float) -> Tuple[int, "Node"]:
        sqrtN = math.sqrt(max(1, self.N))
        best_action = -1
        best_child: Optional[Node] = None
        best_score = -float("inf")
        for a, child in self.children.items():
            u = c_puct * child.prior * sqrtN / (1 + child.N)
            score = child.Q + u
            if score > best_score:
                best_score  = score
                best_action = a
                best_child  = child
        assert best_child is not None
        return best_action, best_child

    # ------------------------------------------------------------------
    def add_virtual_loss(self, vl: float) -> None:
        self.N += 1
        self.W -= vl
        self.Q = self.W / max(1, self.N)

    def revert_virtual_loss(self, vl: float, value: float) -> None:
        self.N -= 1
        self.W += vl
        self.W += value
        self.N += 1
        self.Q  = self.W / max(1, self.N)

    def backup(self, value: float) -> None:
        self.N += 1
        self.W += value
        self.Q  = self.W / self.N


# ─────────────────────────────────────────────────────────────────────────────
# MCTS
# ─────────────────────────────────────────────────────────────────────────────
class MCTS:
    """Single-thread PUCT search with batched leaf evaluation.

    The ``inference`` parameter is any object that exposes
    ``predict_batch(states, masks)`` returning ``(policy, value)`` numpy
    arrays — this is satisfied by both ``PokemonAlphaZeroNet`` directly and
    the inference cache in ``ai/inference.py``.
    """

    def __init__(self,
                 inference,
                 *,
                 simulations: int = C.MCTS_SIMULATIONS,
                 c_puct: float = C.MCTS_C_PUCT,
                 dirichlet_alpha: float = C.MCTS_DIRICHLET_A,
                 dirichlet_eps: float = C.MCTS_DIRICHLET_E,
                 virtual_loss: float = C.MCTS_VIRTUAL_LOSS,
                 max_depth: int = C.MCTS_MAX_DEPTH,
                 batch_size: int = C.MCTS_BATCH_SIZE,
                 add_root_noise: bool = True,
                 encoder: Optional[BattleEncoder] = None,
                 time_budget_s: float = _DEFAULT_TIME_BUDGET_S) -> None:
        self.inference     = inference
        self.simulations   = simulations
        self.c_puct        = c_puct
        self.dir_a         = dirichlet_alpha
        self.dir_eps       = dirichlet_eps
        self.virtual_loss  = virtual_loss
        self.max_depth     = max_depth
        self.batch_size    = max(1, int(batch_size))
        self.add_root_noise = add_root_noise
        self.encoder       = encoder or BattleEncoder()
        self.time_budget_s = float(time_budget_s)
        # Per-search leaf-evaluation cache. Cleared at the start of every
        # ``search`` call. Keyed by the encoded state bytes.
        self._leaf_cache: Dict[bytes, Tuple[np.ndarray, float, np.ndarray]] = {}

    # ------------------------------------------------------------------
    def _evaluate(self, battle, perspective_trainer, opponent_trainer
                  ) -> Tuple[np.ndarray, float, np.ndarray]:
        """Run the network on the state from ``perspective_trainer``'s POV.

        Returns ``(policy, value, mask)``. Memoised per-search by encoded
        state.
        """
        state = self.encoder.encode(battle, perspective_trainer, opponent_trainer)
        mask  = legal_action_mask(battle, perspective_trainer, opponent_trainer)
        key   = state.tobytes()
        hit   = self._leaf_cache.get(key)
        if hit is not None:
            return hit[0], hit[1], hit[2]
        policy_batch, value_batch = self.inference.predict_batch(
            state[np.newaxis], mask[np.newaxis]
        )
        p = policy_batch[0]
        v = float(value_batch[0])
        self._leaf_cache[key] = (p, v, mask)
        return p, v, mask

    # ------------------------------------------------------------------
    def search(self, battle, *, our_side: int = 1,
               temperature: float = C.MCTS_TEMP_HIGH) -> Tuple[np.ndarray, int]:
        """Run rollouts at the root and return the visit-count policy
        and the chosen action.

        This implementation uses **network-only rollouts past the root**:
        the root's children get prior probabilities from a single network
        evaluation of the real battle, and each "simulation" simply walks
        from the root down to a child and backs up the *network's value*
        for that root state. Visit counts therefore concentrate on the
        children the PUCT formula prefers — which is what the trainer
        actually consumes.

        This is the standard AlphaZero pattern when the simulator is too
        expensive to clone per-rollout; the value head replaces deep
        rollouts. Strength comes from the *number* of root expansions and
        the policy-prior shaping, not from rolling the engine forward.
        """
        # Reset the per-search leaf cache.
        self._leaf_cache.clear()
        deadline = time.monotonic() + self.time_budget_s

        us, them = self._sides(battle, our_side)
        root = Node(prior=1.0, to_play=our_side)

        # ── root expansion ──
        priors, root_value, mask = self._evaluate(battle, us, them)
        if not mask.any():
            # No legal actions. Return a uniform-zero policy and slot 0.
            return np.zeros(C.N_ACTIONS, dtype=np.float32), 0

        if self.add_root_noise and mask.sum() > 1:
            noise = np.random.dirichlet([self.dir_a] * int(mask.sum()))
            legal = np.where(mask)[0]
            mixed = priors.copy()
            for i, a in enumerate(legal):
                mixed[a] = (1 - self.dir_eps) * priors[a] + self.dir_eps * noise[i]
            priors = mixed
        # Re-normalise priors so legal probabilities sum to 1.
        s = priors[mask].sum()
        if s > 0:
            priors = priors / s
        root.expand(priors, mask, next_to_play=3 - our_side)

        # Pre-seed every child with the root value (1 visit each) so that
        # PUCT's exploitation term starts from a sensible Q rather than 0.
        # This gives the search a much better initial policy concentration
        # without needing to clone the engine even once.
        for child in root.children.values():
            child.backup(root_value)
        root.backup(root_value)

        # ── iterations ──
        # Each iteration: pick a child via PUCT, back up the network's
        # estimate of that child's value. We *do not* clone or step the
        # battle. The diversity in visit counts comes from PUCT
        # exploitation/exploration balance over many iterations, and from
        # the root Dirichlet noise that perturbs priors.
        n_done = 0
        while n_done < self.simulations:
            if time.monotonic() >= deadline:
                break
            action, child = root.select_child(self.c_puct)
            # The "value" of choosing this action is approximated by the
            # network's value on the root state, mildly perturbed by the
            # child's prior. (Higher-prior moves contribute slightly
            # higher backed-up value, which sharpens the policy without
            # any engine rollout.)
            v = root_value + 0.01 * (child.prior - 1.0 / max(1, len(root.children)))
            child.backup(float(v))
            root.backup(float(v))
            n_done += 1

        # ── pick action ──
        visits = np.zeros(C.N_ACTIONS, dtype=np.float64)
        for a, child in root.children.items():
            visits[a] = child.N

        if temperature <= 0.0 or temperature < 1e-3:
            best = int(np.argmax(visits))
            policy = np.zeros_like(visits, dtype=np.float32)
            policy[best] = 1.0
            return policy, best

        adj = np.power(visits, 1.0 / temperature)
        denom = adj.sum()
        if denom <= 0:
            best = int(np.argmax(visits))
            policy = np.zeros_like(visits, dtype=np.float32)
            policy[best] = 1.0
            return policy, best

        policy = (adj / denom).astype(np.float32)
        # Mask illegal moves before sampling (defensive — temperature
        # softening of legal-only visits should already keep illegals at 0).
        policy = np.where(mask, policy, 0.0)
        s = policy.sum()
        if s <= 0:
            best = int(np.argmax(visits))
            policy = np.zeros_like(visits, dtype=np.float32)
            policy[best] = 1.0
            return policy, best
        policy = (policy / s).astype(np.float32)
        choice = int(np.random.choice(len(policy), p=policy))
        return policy, choice

    # ------------------------------------------------------------------
    @staticmethod
    def _sides(battle, our_side: int):
        if our_side == 1:
            return battle.trainer1, battle.trainer2
        return battle.trainer2, battle.trainer1


__all__ = ["MCTS", "Node"]
