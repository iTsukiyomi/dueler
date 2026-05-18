"""
ai/distributed.py — Multiprocessing self-play coordinator.

Architecture
------------

                ┌────────────────────────┐
                │  Trainer (main proc)   │
                │  • PokemonAlphaZeroNet │
                │  • PrioritizedReplay   │
                │  • InferenceServer ────┼──► request_q ◄─┐
                │                        │                │
                │  ◄── sample_q ─────────┼─────────┐      │
                └────────────────────────┘         │      │
                                                   │      │
   ┌───────────────────────────────────────────────┴──────┴──┐
   │ Self-play worker (N copies)                              │
   │  • RemoteInferenceClient(request_q, response_q_i)        │
   │  • play_one_game(...) → TrajectoryBatch                  │
   │  • puts (states, policies, values, masks) on sample_q    │
   └─────────────────────────────────────────────────────────┘

The trainer process pulls finished trajectories from ``sample_q`` and
inserts them into the replay buffer; meanwhile a background thread
inside the trainer runs the inference server so workers always get
batched evaluations.

Run from the project root with:

    python -m pokemonduel.ai.distributed --workers 6 --device cuda

Stops cleanly on SIGINT.
"""
from __future__ import annotations

import argparse
import logging
import os
import queue
import signal
import sys
import threading
import time
import multiprocessing as mp
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from . import config as C
from .inference import (BatchedInferenceServer, RemoteInferenceClient,
                        _Request)
from .network import PokemonAlphaZeroNet
from .replay_buffer import PrioritizedReplayBuffer
from .selfplay import play_one_game
from .trainer import Trainer

log = logging.getLogger("dueler.ai.distributed")


# ─────────────────────────────────────────────────────────────────────────────
# Worker process entry point
# ─────────────────────────────────────────────────────────────────────────────
def _worker_main(worker_id: int,
                 request_q: Queue,
                 response_q: Queue,
                 sample_q: Queue,
                 stop_flag,
                 games_per_worker: int,
                 simulations: int) -> None:
    logging.basicConfig(level=logging.INFO,
                        format=f"%(asctime)s [w{worker_id}] %(message)s")
    log.info("worker %d up", worker_id)
    np.random.seed(os.getpid() ^ int(time.time()))
    client = RemoteInferenceClient(request_q, response_q, worker_id)
    n_done = 0
    while n_done < games_per_worker and not stop_flag.is_set():
        try:
            traj1, traj2, winner = play_one_game(client, simulations=simulations,
                                                 seed=np.random.randint(2**31))
        except ValueError as e:                                      # unknown pokemon form etc.
            log.warning("game skipped (bad team data): %s", e)
            continue
        except Exception as e:                                       # pragma: no cover
            log.exception("game crashed: %s", e)
            continue
        if traj1.size:
            sample_q.put(traj1.finalise(+1 if winner == 1 else (-1 if winner == 2 else 0)))
        if traj2.size:
            sample_q.put(traj2.finalise(+1 if winner == 2 else (-1 if winner == 1 else 0)))
        n_done += 1
    log.info("worker %d done after %d games", worker_id, n_done)


# ─────────────────────────────────────────────────────────────────────────────
# Coordinator
# ─────────────────────────────────────────────────────────────────────────────
class DistributedTrainer:
    def __init__(self,
                 *,
                 workers: int = C.SELFPLAY_WORKERS,
                 games_per_worker: int = C.SELFPLAY_BATTLES_PER_W,
                 simulations: int = C.MCTS_SIMULATIONS,
                 device: Optional[torch.device] = None) -> None:
        self.workers          = max(1, int(workers))
        self.games_per_worker = int(games_per_worker)
        self.simulations      = int(simulations)
        self.device           = device or C.torch_device()

        self.buffer = PrioritizedReplayBuffer()
        if (C.REPLAY_DIR / "buffer.npz").exists():
            try:
                self.buffer.load(C.REPLAY_DIR / "buffer.npz")
                log.info("Replay buffer loaded: %d samples", len(self.buffer))
            except Exception:
                log.exception("Failed to load replay buffer (continuing fresh)")

        self.trainer = Trainer(self.buffer, device=self.device)

        # Inference server reads from request_q and writes to per-worker
        # response queues. We use a single request queue but a per-worker
        # response queue so the server can target answers correctly.
        # IMPORTANT: all queues are created here (before any fork) so that
        # child processes inherit them via the OS fork – they must NOT be
        # embedded inside _Request objects sent through another queue, as
        # multiprocessing refuses to pickle Queue objects that way.
        self.request_q = Queue(maxsize=4096)
        self.sample_q  = Queue(maxsize=2048)
        # Pre-create one response queue per worker so the inference server
        # has the full dict before any worker process starts.
        self.response_qs: list[Queue] = [Queue(maxsize=4) for _ in range(self.workers)]
        self._procs: list[Process] = []
        self._stop = threading.Event()

    # ------------------------------------------------------------------
    def _start_inference_server(self) -> None:
        server = BatchedInferenceServer(
            self.trainer.net,
            self.request_q,
            {wid: q for wid, q in enumerate(self.response_qs)},
            batch_size=max(8, self.workers * 4),
            max_wait_ms=4.0,
            device=self.device,
        )
        t = threading.Thread(target=server.serve_forever, daemon=True,
                             name="inference-server")
        t.start()
        self._inference_thread = t
        self._inference_server = server

    # ------------------------------------------------------------------
    def _start_workers(self) -> None:
        for wid in range(self.workers):
            rq = self.response_qs[wid]   # already created in __init__
            p = Process(
                target=_worker_main,
                args=(wid, self.request_q, rq, self.sample_q,
                      self._stop, self.games_per_worker, self.simulations),
                name=f"selfplay-{wid}",
                daemon=True,
            )
            p.start()
            self._procs.append(p)
        log.info("Spawned %d self-play workers", self.workers)

    # ------------------------------------------------------------------
    def _drain_sample_q(self) -> None:
        while True:
            try:
                batch = self.sample_q.get(timeout=0.25)
            except queue.Empty:
                continue
            if batch is None:
                return
            states, policies, values, masks = batch
            self.buffer.push_many(states, policies, values, masks)

    # ------------------------------------------------------------------
    def run(self, max_steps: int = C.OPT_TRAIN_STEPS) -> None:
        self._start_inference_server()
        self._start_workers()
        sample_thread = threading.Thread(target=self._drain_sample_q,
                                         daemon=True, name="sample-drain")
        sample_thread.start()

        def _on_sigint(signum, frame):
            log.info("SIGINT received – shutting down ...")
            self._stop.set()
            self._inference_server.stop()
            self.sample_q.put(None)
            sys.exit(0)
        signal.signal(signal.SIGINT, _on_sigint)

        # Persist buffer every ~30s on a background thread.
        def _autosave():
            while not self._stop.is_set():
                time.sleep(60)
                try:
                    self.buffer.save(C.REPLAY_DIR / "buffer.npz")
                except Exception:
                    log.exception("buffer autosave failed")
        threading.Thread(target=_autosave, daemon=True, name="buf-autosave").start()

        try:
            self.trainer.run(max_steps)
        finally:
            self._stop.set()
            self._inference_server.stop()
            for p in self._procs:
                try:
                    p.terminate()
                except Exception:
                    pass
            try:
                self.buffer.save(C.REPLAY_DIR / "buffer.npz")
            except Exception:
                log.exception("final buffer save failed")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="Distributed AlphaZero self-play & training")
    ap.add_argument("--workers", type=int, default=C.SELFPLAY_WORKERS)
    ap.add_argument("--games-per-worker", type=int, default=C.SELFPLAY_BATTLES_PER_W)
    ap.add_argument("--simulations",      type=int, default=C.MCTS_SIMULATIONS)
    ap.add_argument("--steps",            type=int, default=C.OPT_TRAIN_STEPS)
    ap.add_argument("--device",           type=str, default=None)
    ap.add_argument("--run-dir",          type=str, default=None,
                    help="Override DUELER_RUN_DIR (sets where checkpoints land).")
    args = ap.parse_args()

    if args.run_dir:
        os.environ["DUELER_RUN_DIR"] = args.run_dir
        # Re-import config so paths refresh
        import importlib
        importlib.reload(C)

    device = torch.device(args.device) if args.device else None
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    dt = DistributedTrainer(
        workers=args.workers,
        games_per_worker=args.games_per_worker,
        simulations=args.simulations,
        device=device,
    )
    dt.run(max_steps=args.steps)


if __name__ == "__main__":
    mp.set_start_method("fork")
    main()


__all__ = ["DistributedTrainer", "main"]