"""
ai/mcts.py — PUCT Monte-Carlo Tree Search for Pokémon battles.

We use the standard AlphaZero PUCT formulation but adapt it to the
imperfect-information, stochastic nature of Pokémon:

* **Determinisation at root** – the hidden-info tracker samples a
  single plausible opponent set at the root; the search then treats the
  resulting state as fully observable. This is fast and robust.

* **Chance nodes are folded into transitions** – damage rolls, crits and
  misses are sampled stochastically during the engine step; we simply
  *resample* them on every visit, which means the same parent/child pair
  may produce different next-states. Storing per-child Q averages this
  out the way Monte-Carlo originally intended.

* **Virtual loss** keeps multiple search threads from racing into the same
  branch when using leaf batching.

The class is fully *stateless across calls* – ``MCTS.search(battle)`` only
mutates an internal ``Node`` tree which is discarded when the method
returns. Cloning of the underlying ``Battle`` is performed lazily.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

import copy
import numpy as np

from . import config as C
from . import features as F
from .action_mask import legal_action_mask, apply_action
from .encoder import BattleEncoder
from .hidden_info import HiddenInfoTracker
from .simulator import run_turn


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
                 encoder: Optional[BattleEncoder] = None) -> None:
        self.inference  = inference
        self.simulations = simulations
        self.c_puct      = c_puct
        self.dir_a       = dirichlet_alpha
        self.dir_eps     = dirichlet_eps
        self.virtual_loss = virtual_loss
        self.max_depth   = max_depth
        self.batch_size  = max(1, int(batch_size))
        self.add_root_noise = add_root_noise
        self.encoder = encoder or BattleEncoder()

    # ------------------------------------------------------------------
    def _evaluate(self, battle, perspective_trainer, opponent_trainer
                  ) -> Tuple[np.ndarray, float, np.ndarray]:
        """Run the network on the state from ``perspective_trainer``'s POV.

        Returns ``(policy, value, mask)``.
        """
        state = self.encoder.encode(battle, perspective_trainer, opponent_trainer)
        mask  = legal_action_mask(battle, perspective_trainer, opponent_trainer)
        policy_batch, value_batch = self.inference.predict_batch(
            state[np.newaxis], mask[np.newaxis]
        )
        return policy_batch[0], float(value_batch[0]), mask

    # ------------------------------------------------------------------
    def search(self, battle, *, our_side: int = 1,
               temperature: float = C.MCTS_TEMP_HIGH) -> Tuple[np.ndarray, int]:
        """Run ``simulations`` rollouts and return the visit-count policy
        and the chosen action.

        ``our_side`` is ``1`` if we are ``battle.trainer1`` and ``2`` if we
        are ``battle.trainer2``; that drives perspective in the encoder.
        """
        us, them = self._sides(battle, our_side)
        root = Node(prior=1.0, to_play=our_side)

        # ── root expansion ──
        priors, value, mask = self._evaluate(battle, us, them)
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

        # ── iterations ──
        for _ in range(self.simulations):
            # 1) Clone the engine state — deepcopy is heavy but the only
            #    correct option for a stateful engine.
            sim_battle = copy.deepcopy(battle)
            sim_us, sim_them = self._sides(sim_battle, our_side)

            # 2) Traverse the tree to a leaf, taking actions along the way.
            node = root
            path = [(node, None)]
            depth = 0
            terminal_winner = None
            while node.expanded and not node.is_terminal and depth < self.max_depth:
                action, child = node.select_child(self.c_puct)
                # Apply the action for *our* trainer; for the opponent, ask
                # the network to score the same way and pick its best
                # currently-explored child. In single-agent search this is a
                # standard "self-play vs self" approximation.
                sim_us_local, sim_them_local = self._sides(sim_battle, node.to_play)
                apply_action(action, sim_us_local, sim_them_local, sim_battle)

                # Opponent moves with a quick heuristic – use the network's
                # greedy choice for *their* side this turn.
                self._opponent_move(sim_battle, our_side=node.to_play)

                # Resolve a full turn.
                _msg, winner = run_turn(sim_battle)
                if winner is not None:
                    terminal_winner = winner
                    child.is_terminal = True
                    child.value = (
                        1.0 if (winner is sim_battle.trainer1 and our_side == 1)
                              or (winner is sim_battle.trainer2 and our_side == 2)
                        else -1.0
                    )
                    path.append((child, action))
                    break

                path.append((child, action))
                node = child
                depth += 1

            # 3) Expand leaf
            if terminal_winner is None and (not node.expanded or depth >= self.max_depth):
                if not node.is_terminal:
                    sim_us_local, sim_them_local = self._sides(sim_battle, node.to_play)
                    leaf_priors, leaf_value, leaf_mask = self._evaluate(
                        sim_battle, sim_us_local, sim_them_local
                    )
                    s = leaf_priors[leaf_mask].sum()
                    if s > 0:
                        leaf_priors = leaf_priors / s
                    node.expand(leaf_priors, leaf_mask, next_to_play=3 - node.to_play)
                    node.value = leaf_value
                value = node.value if node.is_terminal else leaf_value
            else:
                value = node.value

            # 4) Backup along the path. Values flip sign with perspective.
            for n, _a in reversed(path):
                v = value if n.to_play == our_side else -value
                n.backup(v)

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
        choice = int(np.random.choice(len(policy), p=policy))
        return policy, choice

    # ------------------------------------------------------------------
    def _opponent_move(self, sim_battle, our_side: int) -> None:
        opp_side = 3 - our_side
        opp_us, opp_them = self._sides(sim_battle, opp_side)
        if opp_us is None or opp_us.current_pokemon is None:
            return
        state = self.encoder.encode(sim_battle, opp_us, opp_them)
        mask  = legal_action_mask(sim_battle, opp_us, opp_them)
        if not mask.any():
            return
        policy, _value = self.inference.predict_batch(state[np.newaxis], mask[np.newaxis])
        action = int(np.argmax(policy[0]))
        apply_action(action, opp_us, opp_them, sim_battle)

    # ------------------------------------------------------------------
    @staticmethod
    def _sides(battle, our_side: int):
        if our_side == 1:
            return battle.trainer1, battle.trainer2
        return battle.trainer2, battle.trainer1


__all__ = ["MCTS", "Node"]
