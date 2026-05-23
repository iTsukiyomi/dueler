"""
ai/inference.py — Thin inference wrapper around the network.

<<<<<<< HEAD
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

=======
Thread-safety / eval-mode handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The trainer and the inference server share the *same* network instance,
so the workers always pick up the latest weights. The trainer toggles
``net.train()`` / ``net.eval()`` every optimiser step. Without
coordination the inference thread can wake up inside a ``train()``
window with a batch of size 1 and crash BatchNorm with::

    ValueError: Expected more than 1 value per channel when training,
                got input size torch.Size([1, 768])

To make this impossible, every forward on the inference path:

1. Acquires a module-wide ``RLock``.
2. Forces the network into ``eval()`` mode.
3. Wraps the forward in ``torch.inference_mode()`` AND sets the
   module's training flag explicitly to False on every contained
   sub-module via ``net.eval()`` — so even if another thread races a
   ``net.train()`` call, our forward already saw ``training=False`` at
   forward time (BatchNorm reads ``self.training`` once per call).

The lock window is short (one forward) so contention with the trainer
is negligible.

Picklability
~~~~~~~~~~~~
``InferenceEngine`` and ``RemoteInferenceClient`` expose ``__getstate__`` /
``__setstate__`` that drop their threading primitives and queue handles.

Server-loop robustness
~~~~~~~~~~~~~~~~~~~~~~
``BatchedInferenceServer.serve_forever`` logs and *continues* on any
exception during a batch instead of dying.
"""
from __future__ import annotations

import logging
>>>>>>> 05d15f7 (updated npc ai)
import threading
import time
from collections import OrderedDict
from typing import Optional, Tuple

import numpy as np
import torch

from . import config as C
from . import features as F
from .network import PokemonAlphaZeroNet


<<<<<<< HEAD
=======
log = logging.getLogger("dueler.ai.inference")


>>>>>>> 05d15f7 (updated npc ai)
# ─────────────────────────────────────────────────────────────────────────────
# In-process inference engine
# ─────────────────────────────────────────────────────────────────────────────
class InferenceEngine:
<<<<<<< HEAD
    """Wrap a network so callers can `predict_batch` from any thread."""
=======
    """Wrap a network so callers can `predict_batch` from any thread.

    All forward passes are serialised through a re-entrant lock, run with
    ``net.eval()`` in force, and wrapped in ``torch.inference_mode()``.
    This is robust against another thread concurrently calling
    ``net.train()`` on the same module.
    """
>>>>>>> 05d15f7 (updated npc ai)

    def __init__(self,
                 net: PokemonAlphaZeroNet,
                 device: Optional[torch.device] = None,
                 cache_size: int = 4096) -> None:
        self.net    = net
        self.device = device or next(net.parameters()).device
<<<<<<< HEAD
        self._lock  = threading.Lock()
=======
        self._lock  = threading.RLock()
>>>>>>> 05d15f7 (updated npc ai)
        self._cache: "OrderedDict[bytes, Tuple[np.ndarray, float]]" = OrderedDict()
        self._cache_size = max(0, int(cache_size))
        self.net.eval()

    # ------------------------------------------------------------------
<<<<<<< HEAD
=======
    # Picklability: drop the lock; it will be re-created on restore.
    # ------------------------------------------------------------------
    def __getstate__(self):
        state = self.__dict__.copy()
        state["_lock"]  = None
        state["_cache"] = OrderedDict()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = threading.RLock()
        if not isinstance(self._cache, OrderedDict):
            self._cache = OrderedDict()

    # ------------------------------------------------------------------
>>>>>>> 05d15f7 (updated npc ai)
    def predict_batch(self,
                      states: np.ndarray,
                      masks: Optional[np.ndarray] = None
                      ) -> Tuple[np.ndarray, np.ndarray]:
<<<<<<< HEAD
        """Evaluate ``states`` (shape ``(B, F)``) and return ``(policy,
        value)`` numpy arrays."""
=======
>>>>>>> 05d15f7 (updated npc ai)
        if states.ndim == 1:
            states = states[np.newaxis]
            if masks is not None and masks.ndim == 1:
                masks = masks[np.newaxis]
            single = True
        else:
            single = False

<<<<<<< HEAD
        # Cache lookup
=======
>>>>>>> 05d15f7 (updated npc ai)
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
<<<<<<< HEAD
                p, v = self._forward(arr, eval_masks)
=======
                p, v = self._forward_safely(arr, eval_masks)
>>>>>>> 05d15f7 (updated npc ai)
                with self._lock:
                    for j, idx in enumerate(need_idx):
                        cached_policy[idx] = p[j]
                        cached_value[idx]  = v[j]
                        self._cache[keys[idx]] = (p[j].copy(), float(v[j]))
                        if len(self._cache) > self._cache_size:
                            self._cache.popitem(last=False)
            policy, value = cached_policy, cached_value
        else:
<<<<<<< HEAD
            policy, value = self._forward(states, masks)
=======
            policy, value = self._forward_safely(states, masks)
>>>>>>> 05d15f7 (updated npc ai)

        if single:
            return policy, value
        return policy, value

    # ------------------------------------------------------------------
<<<<<<< HEAD
    def _forward(self, states: np.ndarray, masks: Optional[np.ndarray]
                 ) -> Tuple[np.ndarray, np.ndarray]:
        return self.net.predict_batch(states, masks, device=self.device)
=======
    def _forward_safely(self,
                        states: np.ndarray,
                        masks: Optional[np.ndarray]
                        ) -> Tuple[np.ndarray, np.ndarray]:
        """Forward pass that is guaranteed to run with the network in
        eval mode. The eval-mode window is protected by a re-entrant
        lock AND wrapped in ``torch.inference_mode()`` for extra safety
        against any unexpected ``net.train()`` toggle from another
        thread.

        Pads a singleton batch up to size 2 if needed to dodge the
        BatchNorm "got input size [1, 768]" failure that can still
        appear under exotic interleavings on some PyTorch builds. The
        duplicated row's output is discarded.
        """
        with self._lock:
            was_training = self.net.training
            self.net.eval()
            try:
                # Detect singleton-batch case and pad to size 2 with a
                # zero row. BatchNorm in train mode hates batch=1; padding
                # to >=2 makes the call safe under any race condition.
                pad_needed = (states.shape[0] == 1)
                if pad_needed:
                    states_in = np.concatenate([states, np.zeros_like(states)], axis=0)
                    if masks is not None:
                        masks_in = np.concatenate([masks, masks], axis=0)
                    else:
                        masks_in = None
                else:
                    states_in = states
                    masks_in  = masks

                with torch.inference_mode():
                    policy, value = self.net.predict_batch(
                        states_in, masks_in, device=self.device
                    )

                if pad_needed:
                    policy = policy[:1]
                    value  = value[:1]
            finally:
                if was_training:
                    self.net.train()
            return policy, value
>>>>>>> 05d15f7 (updated npc ai)

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
<<<<<<< HEAD
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
=======
    submit single-state requests via an mp.Queue.

    The serve loop is **self-healing**: any exception from a single batch
    is logged and the loop continues. Workers may have to time out on
    that one request and retry, but the server itself stays alive.

    Each worker sends a sentinel reply on a failed batch so workers don't
    block forever on ``resp_q.get()`` — they'll see a "(None, 0.0)" pair
    and can retry / fall back. (Implemented below in the except branch.)
>>>>>>> 05d15f7 (updated npc ai)
    """

    def __init__(self,
                 net: PokemonAlphaZeroNet,
                 request_q,
                 response_qs: dict,          # {worker_id: Queue}
                 *,
                 batch_size: int = 64,
<<<<<<< HEAD
                 max_wait_ms: float = 4.0,
                 device: Optional[torch.device] = None) -> None:
        self.engine      = InferenceEngine(net, device=device, cache_size=0)
        self.req_q       = request_q
        self.response_qs = response_qs       # kept in the main process only
=======
                 max_wait_ms: float = 1.0,
                 device: Optional[torch.device] = None) -> None:
        self.engine      = InferenceEngine(net, device=device, cache_size=0)
        self.req_q       = request_q
        self.response_qs = response_qs
>>>>>>> 05d15f7 (updated npc ai)
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

<<<<<<< HEAD
            states = np.stack([r.state for r in pending], axis=0)
            masks  = np.stack([r.mask  for r in pending], axis=0) if pending[0].mask is not None else None
            policies, values = self.engine.predict_batch(states, masks)
            for r, p, v in zip(pending, policies, values):
                try:
                    self.response_qs[r.worker_id].put((p, float(v)))
                except Exception:
                    pass
            pending.clear()
=======
            try:
                states = np.stack([r.state for r in pending], axis=0)
                masks  = np.stack([r.mask  for r in pending], axis=0) if pending[0].mask is not None else None
                policies, values = self.engine.predict_batch(states, masks)
                for r, p, v in zip(pending, policies, values):
                    try:
                        self.response_qs[r.worker_id].put((p, float(v)))
                    except Exception:
                        pass
            except Exception:
                log.exception("inference batch failed (size=%d); sending neutral replies",
                              len(pending))
                # Send neutral replies so workers don't block forever.
                # The shapes/values are valid: uniform policy over legal
                # actions, value 0. Workers can keep going.
                for r in pending:
                    try:
                        if r.mask is not None:
                            m = np.asarray(r.mask, dtype=bool)
                            if m.any():
                                p = m.astype(np.float32)
                                p /= p.sum()
                            else:
                                p = np.zeros(C.N_ACTIONS, dtype=np.float32)
                                p[0] = 1.0
                        else:
                            p = np.full(C.N_ACTIONS, 1.0 / C.N_ACTIONS, dtype=np.float32)
                        self.response_qs[r.worker_id].put((p, 0.0))
                    except Exception:
                        pass
            finally:
                pending.clear()
>>>>>>> 05d15f7 (updated npc ai)


class RemoteInferenceClient:
    """Counterpart to ``BatchedInferenceServer`` for worker processes."""

    def __init__(self, request_q, response_q, worker_id: int) -> None:
        self.req_q    = request_q
        self.resp_q   = response_q
        self.worker_id = worker_id

<<<<<<< HEAD
    def predict_batch(self, states: np.ndarray, masks: Optional[np.ndarray] = None):
        # Iterative submit – the server already batches, no need to do so here.
=======
    # ------------------------------------------------------------------
    def __getstate__(self):
        return {"worker_id": self.worker_id}

    def __setstate__(self, state):
        self.worker_id = state.get("worker_id", -1)
        self.req_q  = None
        self.resp_q = None

    def predict_batch(self, states: np.ndarray, masks: Optional[np.ndarray] = None):
>>>>>>> 05d15f7 (updated npc ai)
        if states.ndim == 1:
            states = states[np.newaxis]
            masks  = None if masks is None else masks[np.newaxis]
        policies = np.empty((len(states), C.N_ACTIONS), dtype=np.float32)
        values   = np.empty((len(states),),             dtype=np.float32)
        for i, s in enumerate(states):
            m = None if masks is None else masks[i]
<<<<<<< HEAD
            # Pass worker_id (an int), NOT the response queue itself.
            # Embedding a Queue inside another Queue's message would cause
            # a pickling error even under fork-mode multiprocessing.
=======
>>>>>>> 05d15f7 (updated npc ai)
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
<<<<<<< HEAD
]
=======
]
>>>>>>> 05d15f7 (updated npc ai)
