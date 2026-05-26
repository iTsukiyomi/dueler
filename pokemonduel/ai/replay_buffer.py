"""
ai/replay_buffer.py — Prioritised replay with compressed persistence.

Each entry is a tuple ``(state, policy_target, value_target)`` where
``state`` is the feature vector emitted by ``BattleEncoder``, ``policy_target``
is the MCTS visit distribution (sum == 1, illegal entries zero) and
``value_target`` is the eventual game-result from the current player's
point of view in ``[-1, +1]``.

The buffer is implemented over pre-allocated numpy arrays so push/sample
operations are O(1). Priorities are stored in a min-heap-style sum-tree to
allow proportional sampling in O(log N).

Compressed snapshots are saved as ``.npz`` files via ``save()`` /
``load()`` so a training run can be resumed without losing experience.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Tuple

import numpy as np

from . import config as C
from . import features as F


# ─────────────────────────────────────────────────────────────────────────────
# Sum-tree for proportional prioritised sampling
# ─────────────────────────────────────────────────────────────────────────────
class _SumTree:
    """Pure-python sum-tree compatible with PER (Schaul et al., 2015)."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity, dtype=np.float64)
        self.size = 0
        self.cursor = 0

    def total(self) -> float:
        return float(self.tree[1])

    def add(self, priority: float) -> int:
        idx = self.cursor + self.capacity
        self.update(idx, priority)
        self.cursor = (self.cursor + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
        return idx - self.capacity

    def update(self, tree_idx: int, priority: float) -> None:
        change = priority - self.tree[tree_idx]
        self.tree[tree_idx] = priority
        # propagate up
        parent = tree_idx >> 1
        while parent:
            self.tree[parent] += change
            parent >>= 1

    def get_leaf(self, s: float) -> Tuple[int, float]:
        idx = 1
        while idx < self.capacity:
            left = 2 * idx
            right = left + 1
            if s <= self.tree[left]:
                idx = left
            else:
                s -= self.tree[left]
                idx = right
        return idx, float(self.tree[idx])


# ─────────────────────────────────────────────────────────────────────────────
# Prioritised replay buffer
# ─────────────────────────────────────────────────────────────────────────────
class PrioritizedReplayBuffer:
    """Thread-safe prioritised replay buffer used by the trainer."""

    def __init__(self,
                 capacity: int = C.REPLAY_CAPACITY,
                 alpha: float = C.REPLAY_ALPHA,
                 beta_start: float = C.REPLAY_BETA_START,
                 beta_end: float = C.REPLAY_BETA_END,
                 beta_steps: int = C.REPLAY_BETA_STEPS,
                 eps: float = C.REPLAY_EPS,
                 feature_dim: int = F.FEATURE_DIM,
                 n_actions: int = C.N_ACTIONS) -> None:
        self.capacity   = int(capacity)
        self.alpha      = float(alpha)
        self.beta_start = float(beta_start)
        self.beta_end   = float(beta_end)
        self.beta_steps = int(beta_steps)
        self.eps        = float(eps)
        self.feature_dim = int(feature_dim)
        self.n_actions   = int(n_actions)
        self._step       = 0

        self._states  = np.zeros((self.capacity, self.feature_dim), dtype=np.float32)
        self._policy  = np.zeros((self.capacity, self.n_actions),   dtype=np.float32)
        self._values  = np.zeros((self.capacity,),                  dtype=np.float32)
        self._masks   = np.zeros((self.capacity, self.n_actions),   dtype=bool)
        self._tree    = _SumTree(self.capacity)
        self._max_pri = 1.0
        self._lock    = threading.RLock()

    # ──────────────────────────────────────────────────────────────────
    def __len__(self) -> int:
        return self._tree.size

    # ──────────────────────────────────────────────────────────────────
    def push(self,
             state: np.ndarray,
             policy: np.ndarray,
             value: float,
             mask: np.ndarray | None = None,
             priority: float | None = None) -> None:
        if state.shape[0] != self.feature_dim:
            raise ValueError(f"state has wrong dim: {state.shape[0]} vs {self.feature_dim}")
        if policy.shape[0] != self.n_actions:
            raise ValueError("policy has wrong dim")

        with self._lock:
            idx = self._tree.add(self._max_pri ** self.alpha
                                 if priority is None
                                 else max(priority, self.eps) ** self.alpha)
            self._states[idx] = state
            self._policy[idx] = policy
            self._values[idx] = float(value)
            if mask is None:
                self._masks[idx] = True
            else:
                self._masks[idx] = mask.astype(bool)

    # ──────────────────────────────────────────────────────────────────
    def push_many(self, states, policies, values, masks=None) -> None:
        for i in range(len(states)):
            self.push(states[i], policies[i], float(values[i]),
                      None if masks is None else masks[i])

    # ──────────────────────────────────────────────────────────────────
    def sample(self, batch_size: int):
        if self._tree.size == 0:
            raise RuntimeError("buffer is empty")
        with self._lock:
            total = self._tree.total()
            seg   = total / batch_size
            idxs  = np.empty(batch_size, dtype=np.int64)
            tree_idxs = np.empty(batch_size, dtype=np.int64)
            pris  = np.empty(batch_size, dtype=np.float64)

            for i in range(batch_size):
                s = np.random.uniform(seg * i, seg * (i + 1))
                tidx, p = self._tree.get_leaf(s)
                pris[i] = p
                tree_idxs[i] = tidx
                idxs[i] = tidx - self._tree.capacity

            beta = self._current_beta()
            probs = pris / max(total, 1e-12)
            weights = (self._tree.size * probs) ** (-beta)
            weights = weights / max(weights.max(), 1e-12)

            self._step += 1
            return (
                self._states[idxs].copy(),
                self._policy[idxs].copy(),
                self._values[idxs].copy(),
                self._masks[idxs].copy(),
                weights.astype(np.float32),
                tree_idxs,
            )

    # ──────────────────────────────────────────────────────────────────
    def update_priorities(self, tree_idxs, td_errors) -> None:
        with self._lock:
            for ti, err in zip(tree_idxs, td_errors):
                p = (abs(float(err)) + self.eps) ** self.alpha
                self._tree.update(int(ti), p)
                self._max_pri = max(self._max_pri, float(p))

    # ──────────────────────────────────────────────────────────────────
    def _current_beta(self) -> float:
        if self.beta_steps <= 0:
            return self.beta_end
        frac = min(1.0, self._step / self.beta_steps)
        return self.beta_start + (self.beta_end - self.beta_start) * frac

    # ──────────────────────────────────────────────────────────────────
    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            _tmp = str(path) + ".tmp"
            np.savez_compressed(
                _tmp,
                states  = self._states[: self._tree.size],
                policy  = self._policy[: self._tree.size],
                values  = self._values[: self._tree.size],
                masks   = self._masks[: self._tree.size],
                tree    = self._tree.tree,
                size    = np.int64(self._tree.size),
                cursor  = np.int64(self._tree.cursor),
                max_pri = np.float64(self._max_pri),
                step    = np.int64(self._step),
            )
            os.replace(_tmp + ".npz", str(path))

    # ──────────────────────────────────────────────────────────────────
    def load(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists():
            return False
        with self._lock:
            data = np.load(path, allow_pickle=False)
            n = int(data["size"])
            self._states[:n] = data["states"]
            self._policy[:n] = data["policy"]
            self._values[:n] = data["values"]
            self._masks [:n] = data["masks"]
            self._tree.tree  = data["tree"]
            self._tree.size  = n
            self._tree.cursor = int(data["cursor"])
            self._max_pri    = float(data["max_pri"])
            self._step       = int(data["step"])
        return True


# ─────────────────────────────────────────────────────────────────────────────
# In-memory queue-based intermediate buffer used to ship samples from
# self-play workers (separate processes) to the trainer over IPC.
# ─────────────────────────────────────────────────────────────────────────────
class TrajectoryBatch:
    """A whole game's worth of (state, policy_target) tuples plus the
    eventual winner-side value. Filled by the self-play loop, then drained
    into a ``PrioritizedReplayBuffer`` once the game ends."""

    __slots__ = ("states", "policies", "masks", "to_play", "size")

    def __init__(self) -> None:
        self.states:   list = []
        self.policies: list = []
        self.masks:    list = []
        self.to_play:  list = []
        self.size = 0

    def add(self, state: np.ndarray, policy: np.ndarray,
            mask: np.ndarray, to_play: int) -> None:
        self.states.append(state)
        self.policies.append(policy)
        self.masks.append(mask)
        self.to_play.append(to_play)
        self.size += 1

    def finalise(self, winner_side: int):
        """Compute z values and return parallel arrays.

        ``winner_side`` is ``+1`` if trainer1 won, ``-1`` if trainer2 won,
        and ``0`` on a draw. Each transition's value target is the win
        signal from *that* turn's player perspective.
        """
        values = []
        for p in self.to_play:
            values.append(winner_side if p == 1 else (-winner_side if p == 2 else 0.0))
        return (np.asarray(self.states,   dtype=np.float32),
                np.asarray(self.policies, dtype=np.float32),
                np.asarray(values,        dtype=np.float32),
                np.asarray(self.masks,    dtype=bool))


__all__ = ["PrioritizedReplayBuffer", "TrajectoryBatch"]
