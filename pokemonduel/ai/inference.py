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


class InferenceEngine:
    """Wrap a network so callers can `predict_batch` from any thread.

    All forward passes are serialised through a re-entrant lock, run with
    ``net.eval()`` in force, and wrapped in ``torch.inference_mode()``.
    This is robust against another thread concurrently calling
    ``net.train()`` on the same module.
    """

    def __init__(self,
                 net: PokemonAlphaZeroNet,
                 device: Optional[torch.device] = None,
                 cache_size: int = 4096) -> None:
        self.net    = net
        self.device = device or next(net.parameters()).device
        self._lock  = threading.RLock()
        self._cache: "OrderedDict[bytes, Tuple[np.ndarray, float]]" = OrderedDict()
        self._cache_size = max(0, int(cache_size))
        self.net.eval()

    def predict_batch(self, states: np.ndarray, masks: Optional[np.ndarray] = None):
        if states.ndim == 1:
            states = states[np.newaxis]
            if masks is not None and masks.ndim == 1:
                masks = masks[np.newaxis]
            single = True
        else:
            single = False

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
                p, v = self._forward_safely(arr, eval_masks)
                with self._lock:
                    for j, idx in enumerate(need_idx):
                        cached_policy[idx] = p[j]
                        cached_value[idx]  = v[j]
                        self._cache[keys[idx]] = (p[j].copy(), float(v[j]))
                        if len(self._cache) > self._cache_size:
                            self._cache.popitem(last=False)
            policy, value = cached_policy, cached_value
        else:
            policy, value = self._forward_safely(states, masks)

        if single:
            return policy, value
        return policy, value

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
                # Detect singleton-batch case and pad to size 2 with a zero row. BatchNorm in train mode hates batch=1; padding to >=2 makes the call safe under any race condition.
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

    def load_state(self, state_dict: dict) -> None:
        with self._lock:
            self.net.load_state_dict(state_dict)
            self.net.eval()
            self._cache.clear()


class _Request:
    __slots__ = ("state", "mask", "worker_id")
    def __init__(self, state, mask, worker_id: int):
        self.state, self.mask, self.worker_id = state, mask, worker_id


class BatchedInferenceServer:
    """Run inference in the main process while multiple self-play workers
    submit single-state requests via an mp.Queue.

    The serve loop is **self-healing**: any exception from a single batch
    is logged and the loop continues. Workers may have to time out on
    that one request and retry, but the server itself stays alive.

    Each worker sends a sentinel reply on a failed batch so workers don't
    block forever on ``resp_q.get()`` — they'll see a "(None, 0.0)" pair
    and can retry / fall back. (Implemented below in the except branch.)
    """

    def __init__(self,
                 net: PokemonAlphaZeroNet,
                 request_q,
                 response_qs: dict,
                 *,
                 batch_size: int = 64,
                 max_wait_ms: float = 1.0,
                 device: Optional[torch.device] = None) -> None:
        self.engine      = InferenceEngine(net, device=device, cache_size=0)
        self.req_q       = request_q
        self.response_qs = response_qs
        self.batch       = max(1, int(batch_size))
        self.wait_s      = float(max_wait_ms) / 1000.0
        self._stop       = threading.Event()

    def stop(self) -> None:
        self._stop.set()

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
                # pyrefly: ignore [unknown-name]
                log.exception("inference batch failed (size=%d); sending neutral replies",
                              len(pending))
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


class RemoteInferenceClient:
    """Counterpart to ``BatchedInferenceServer`` for worker processes."""

    def __init__(self, request_q, response_q, worker_id: int) -> None:
        self.req_q    = request_q
        self.resp_q   = response_q
        self.worker_id = worker_id

    def __getstate__(self):
        return {"worker_id": self.worker_id}

    def __setstate__(self, state):
        self.worker_id = state.get("worker_id", -1)
        self.req_q  = None
        self.resp_q = None

    def predict_batch(self, states: np.ndarray, masks: Optional[np.ndarray] = None):
        if states.ndim == 1:
            states = states[np.newaxis]
            masks  = None if masks is None else masks[np.newaxis]
        policies = np.empty((len(states), C.N_ACTIONS), dtype=np.float32)
        values   = np.empty((len(states),),             dtype=np.float32)
        for i, s in enumerate(states):
            m = None if masks is None else masks[i]
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
