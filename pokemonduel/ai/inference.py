"""
ai/inference.py — Thin inference wrapper around the network.

Provides:

* ``InferenceEngine``      – wraps a ``PokemonAlphaZeroNet`` with thread-safe
                             batched ``predict_batch`` calls and an optional
                             tiny LRU cache for repeated states (handy for
                             MCTS where leaf evaluations sometimes hit the
                             same canonical encoding).

* ``BatchedInferenceServer`` – multiprocess-safe inference server that
                             batches requests across multiple self-play
                             workers using a request/response queue. Used
                             by ``ai/distributed.py``.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Optional, Tuple

import numpy as np
import torch

from . import config as C
from . import features as F
from .network import PokemonAlphaZeroNet


# ─────────────────────────────────────────────────────────────────────────────
# In-process inference engine
# ─────────────────────────────────────────────────────────────────────────────
class InferenceEngine:
    """Wrap a network so callers can `predict_batch` from any thread."""

    def __init__(self,
                 net: PokemonAlphaZeroNet,
                 device: Optional[torch.device] = None,
                 cache_size: int = 4096) -> None:
        self.net    = net
        self.device = device or next(net.parameters()).device
        self._lock  = threading.Lock()
        self._cache: "OrderedDict[bytes, Tuple[np.ndarray, float]]" = OrderedDict()
        self._cache_size = max(0, int(cache_size))
        self.net.eval()

    # ------------------------------------------------------------------
    def predict_batch(self,
                      states: np.ndarray,
                      masks: Optional[np.ndarray] = None
                      ) -> Tuple[np.ndarray, np.ndarray]:
        """Evaluate ``states`` (shape ``(B, F)``) and return ``(policy,
        value)`` numpy arrays."""
        if states.ndim == 1:
            states = states[np.newaxis]
            if masks is not None and masks.ndim == 1:
                masks = masks[np.newaxis]
            single = True
        else:
            single = False

        # Cache lookup
        if self._cache_size > 0:
            cached_policy = np.empty((states.shape[0], C.N_ACTIONS), dtype=np.float32)
            cached_value  = np.empty((states.shape[0],),              dtype=np.float32)
            need_eval = []
            need_idx  = []
            keys      = []
            with self._lock:
                for i, s in enumerate(states):
                    k = s.tobytes()
                    keys.append(k)
                    hit = self._cache.get(k)
                    if hit is not None:
                        cached_policy[i] = hit[0]
                        cached_value[i]  = hit[1]
                    else:
                        need_eval.append(s)
                        need_idx.append(i)
            if need_eval:
                arr = np.asarray(need_eval, dtype=np.float32)
                eval_masks = None
                if masks is not None:
                    eval_masks = masks[need_idx]
                p, v = self._forward(arr, eval_masks)
                with self._lock:
                    for j, idx in enumerate(need_idx):
                        cached_policy[idx] = p[j]
                        cached_value[idx]  = v[j]
                        self._cache[keys[idx]] = (p[j].copy(), float(v[j]))
                        if len(self._cache) > self._cache_size:
                            self._cache.popitem(last=False)
            policy, value = cached_policy, cached_value
        else:
            policy, value = self._forward(states, masks)

        if single:
            return policy, value
        return policy, value

    # ------------------------------------------------------------------
    def _forward(self, states: np.ndarray, masks: Optional[np.ndarray]
                 ) -> Tuple[np.ndarray, np.ndarray]:
        return self.net.predict_batch(states, masks, device=self.device)

    # ------------------------------------------------------------------
    def load_state(self, state_dict: dict) -> None:
        with self._lock:
            self.net.load_state_dict(state_dict)
            self.net.eval()
            self._cache.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Batched cross-process inference server
# ─────────────────────────────────────────────────────────────────────────────
class _Request:
    __slots__ = ("state", "mask", "worker_id")
    def __init__(self, state, mask, worker_id: int):
        self.state, self.mask, self.worker_id = state, mask, worker_id


class BatchedInferenceServer:
    """Run inference in the main process while multiple self-play workers
    submit single-state requests via an mp.Queue. The server collects up to
    ``batch_size`` pending requests, runs one forward pass, and dispatches
    answers back through per-worker response queues.

    Construct it with the *network instance* (already on the GPU/CPU), a
    *request_queue* shared with the workers, and a mapping of
    ``worker_id -> response_queue``. Call ``serve_forever`` in its own
    thread / process.

    Note: response queues must NOT be embedded inside ``_Request`` objects
    because multiprocessing queues cannot be pickled (serialised into another
    queue's pipe). Pass them here at construction time instead.
    """

    def __init__(self,
                 net: PokemonAlphaZeroNet,
                 request_q,
                 response_qs: dict,          # {worker_id: Queue}
                 *,
                 batch_size: int = 64,
                 max_wait_ms: float = 4.0,
                 device: Optional[torch.device] = None) -> None:
        self.engine      = InferenceEngine(net, device=device, cache_size=0)
        self.req_q       = request_q
        self.response_qs = response_qs       # kept in the main process only
        self.batch       = max(1, int(batch_size))
        self.wait_s      = float(max_wait_ms) / 1000.0
        self._stop       = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    # ------------------------------------------------------------------
    def serve_forever(self) -> None:
        pending: list[_Request] = []
        while not self._stop.is_set():
            try:
                first = self.req_q.get(timeout=0.25)
            except Exception:
                continue
            if first is None:
                self._stop.set()
                break
            pending.append(first)
            deadline = time.monotonic() + self.wait_s
            while len(pending) < self.batch and time.monotonic() < deadline:
                try:
                    r = self.req_q.get_nowait()
                except Exception:
                    break
                if r is None:
                    self._stop.set()
                    break
                pending.append(r)

            states = np.stack([r.state for r in pending], axis=0)
            masks  = np.stack([r.mask  for r in pending], axis=0) if pending[0].mask is not None else None
            policies, values = self.engine.predict_batch(states, masks)
            for r, p, v in zip(pending, policies, values):
                try:
                    self.response_qs[r.worker_id].put((p, float(v)))
                except Exception:
                    pass
            pending.clear()


class RemoteInferenceClient:
    """Counterpart to ``BatchedInferenceServer`` for worker processes."""

    def __init__(self, request_q, response_q, worker_id: int) -> None:
        self.req_q    = request_q
        self.resp_q   = response_q
        self.worker_id = worker_id

    def predict_batch(self, states: np.ndarray, masks: Optional[np.ndarray] = None):
        # Iterative submit – the server already batches, no need to do so here.
        if states.ndim == 1:
            states = states[np.newaxis]
            masks  = None if masks is None else masks[np.newaxis]
        policies = np.empty((len(states), C.N_ACTIONS), dtype=np.float32)
        values   = np.empty((len(states),),             dtype=np.float32)
        for i, s in enumerate(states):
            m = None if masks is None else masks[i]
            # Pass worker_id (an int), NOT the response queue itself.
            # Embedding a Queue inside another Queue's message would cause
            # a pickling error even under fork-mode multiprocessing.
            self.req_q.put(_Request(s.astype(np.float32, copy=True),
                                    None if m is None else m.copy(),
                                    self.worker_id))
            p, v = self.resp_q.get()
            policies[i] = p
            values[i]   = v
        return policies, values


__all__ = [
    "InferenceEngine",
    "BatchedInferenceServer",
    "RemoteInferenceClient",
]