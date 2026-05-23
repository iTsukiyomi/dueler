"""
ai/distributed.py — Multiprocessing self-play coordinator.

<<<<<<< HEAD
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
=======
Robustness features
~~~~~~~~~~~~~~~~~~~
* **Per-game wall-clock timeout.** Workers that hang on pathological
  states give up after ``SELFPLAY_GAME_TIMEOUT_S`` (default 90 s).
* **Self-healing inference server.** A watchdog restarts the inference
  thread if it ever exits.
* **Low-latency batching** (``batch_size = workers``, ``max_wait_ms = 1``).
* **Discord live-buffer ingestion.** On startup the trainer loads the
  self-play buffer AND the Discord ``live_buffer.npz`` (if it exists),
  merging both sources into the same replay buffer. The live buffer is
  also re-checked every ``LIVE_BUFFER_POLL_S`` seconds at runtime so
  freshly-played Discord battles enter training without restart.
>>>>>>> 05d15f7 (updated npc ai)
"""
from __future__ import annotations

import argparse
import logging
<<<<<<< HEAD
=======
import multiprocessing as mp
>>>>>>> 05d15f7 (updated npc ai)
import os
import queue
import signal
import sys
import threading
import time
<<<<<<< HEAD
import multiprocessing as mp
from multiprocessing import Process, Queue
=======
from multiprocessing import Process, Queue, Value
>>>>>>> 05d15f7 (updated npc ai)
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


<<<<<<< HEAD
=======
_GAME_TIMEOUT_S      = float(getattr(C, "SELFPLAY_GAME_TIMEOUT_S", 90.0))
_LIVE_BUFFER_POLL_S  = float(getattr(C, "LIVE_BUFFER_POLL_S", 60.0))

# Paths to the two on-disk buffers.
_SELFPLAY_BUFFER_PATH = C.REPLAY_DIR / "buffer.npz"
_LIVE_BUFFER_PATH     = C.REPLAY_DIR / "live_buffer.npz"


# ─────────────────────────────────────────────────────────────────────────────
def _merge_buffer_from_disk(target: PrioritizedReplayBuffer,
                            path: Path) -> int:
    """Load samples from ``path`` and ``push_many`` them into ``target``.

    Returns the number of samples merged (0 if the file doesn't exist or
    can't be read). Uses ``push_many`` instead of ``load`` so the
    existing samples in ``target`` are preserved.
    """
    if not path.exists():
        return 0
    try:
        data = np.load(path, allow_pickle=False)
        n = int(data["size"])
        if n <= 0:
            return 0
        states   = data["states"][:n]
        policies = data["policy"][:n]
        values   = data["values"][:n]
        masks    = data["masks"][:n]
        target.push_many(states, policies, values, masks)
        return n
    except Exception:
        log.exception("Failed to merge buffer from %s", path)
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Shared progress counters (one set per WorkerStats namespace)
# ─────────────────────────────────────────────────────────────────────────────
class WorkerStats:
    __slots__ = ("games_done", "games_crashed", "games_skipped",
                 "games_timed_out",
                 "turns_total", "sims_total", "last_heartbeat",
                 "alive")

    def __init__(self) -> None:
        self.games_done      = Value("i", 0)
        self.games_crashed   = Value("i", 0)
        self.games_skipped   = Value("i", 0)
        self.games_timed_out = Value("i", 0)
        self.turns_total     = Value("i", 0)
        self.sims_total      = Value("q", 0)
        self.last_heartbeat  = Value("d", 0.0)
        self.alive           = Value("i", 1)


>>>>>>> 05d15f7 (updated npc ai)
# ─────────────────────────────────────────────────────────────────────────────
# Worker process entry point
# ─────────────────────────────────────────────────────────────────────────────
def _worker_main(worker_id: int,
                 request_q: Queue,
                 response_q: Queue,
                 sample_q: Queue,
                 stop_flag,
                 games_per_worker: int,
<<<<<<< HEAD
                 simulations: int) -> None:
=======
                 simulations: int,
                 stats: WorkerStats) -> None:
>>>>>>> 05d15f7 (updated npc ai)
    logging.basicConfig(level=logging.INFO,
                        format=f"%(asctime)s [w{worker_id}] %(message)s")
    log.info("worker %d up", worker_id)
    np.random.seed(os.getpid() ^ int(time.time()))
    client = RemoteInferenceClient(request_q, response_q, worker_id)
<<<<<<< HEAD
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
=======

    with stats.alive.get_lock():
        stats.alive.value = 1
    with stats.last_heartbeat.get_lock():
        stats.last_heartbeat.value = time.time()

    n_done = 0
    while n_done < games_per_worker and not stop_flag.is_set():
        game_t0 = time.time()
        with stats.last_heartbeat.get_lock():
            stats.last_heartbeat.value = game_t0

        try:
            result = _play_one_game_with_timeout(
                client, simulations, stats, _GAME_TIMEOUT_S
            )
        except ValueError as e:
            log.warning("worker %d skipped (bad team data): %s", worker_id, e)
            with stats.games_skipped.get_lock():
                stats.games_skipped.value += 1
            continue
        except Exception as e:
            # Common case: simulator hits a KeyError on a rare form whose
            # base_stats lookup fails. We log once (full traceback) so
            # it's visible, then count as skipped and continue. The
            # pokemon_send_out.py patch in this repo makes most of these
            # non-fatal, but we keep the guard as defence in depth.
            log.exception("worker %d game error (skipping): %s", worker_id, e)
            with stats.games_crashed.get_lock():
                stats.games_crashed.value += 1
            continue

        if result is None:
            with stats.games_timed_out.get_lock():
                stats.games_timed_out.value += 1
            log.warning("worker %d game timed out after %.0fs; starting fresh",
                        worker_id, _GAME_TIMEOUT_S)
            continue

        traj1, traj2, winner = result
        dt = time.time() - game_t0
        turns = max(traj1.size, traj2.size)
        with stats.games_done.get_lock():
            stats.games_done.value += 1
        with stats.turns_total.get_lock():
            stats.turns_total.value += turns
        log.info("worker %d game %d done: winner=%s turns=%d in %.1fs",
                 worker_id, n_done, winner, turns, dt)
>>>>>>> 05d15f7 (updated npc ai)
        if traj1.size:
            sample_q.put(traj1.finalise(+1 if winner == 1 else (-1 if winner == 2 else 0)))
        if traj2.size:
            sample_q.put(traj2.finalise(+1 if winner == 2 else (-1 if winner == 1 else 0)))
        n_done += 1
<<<<<<< HEAD
    log.info("worker %d done after %d games", worker_id, n_done)
=======

    log.info("worker %d done after %d games", worker_id, n_done)
    with stats.alive.get_lock():
        stats.alive.value = 0


def _play_one_game_with_timeout(client, simulations: int,
                                stats: "WorkerStats",
                                timeout_s: float):
    box: dict = {}

    def _runner():
        try:
            box["result"] = play_one_game(
                client,
                simulations=simulations,
                seed=int(np.random.randint(2**31)),
                progress_cb=lambda turn: _worker_progress(stats, turn, simulations),
            )
        except BaseException as e:
            box["exc"] = e

    t = threading.Thread(target=_runner, daemon=True, name="game-runner")
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        return None
    if "exc" in box:
        raise box["exc"]
    return box.get("result")


def _worker_progress(stats: WorkerStats, turn: int, simulations: int) -> None:
    with stats.sims_total.get_lock():
        stats.sims_total.value += 2 * simulations
    with stats.last_heartbeat.get_lock():
        stats.last_heartbeat.value = time.time()
>>>>>>> 05d15f7 (updated npc ai)


# ─────────────────────────────────────────────────────────────────────────────
# Coordinator
# ─────────────────────────────────────────────────────────────────────────────
class DistributedTrainer:
    def __init__(self,
                 *,
                 workers: int = C.SELFPLAY_WORKERS,
                 games_per_worker: int = C.SELFPLAY_BATTLES_PER_W,
                 simulations: int = C.MCTS_SIMULATIONS,
<<<<<<< HEAD
                 device: Optional[torch.device] = None) -> None:
=======
                 device: Optional[torch.device] = None,
                 heartbeat_period: float = 2.0) -> None:
>>>>>>> 05d15f7 (updated npc ai)
        self.workers          = max(1, int(workers))
        self.games_per_worker = int(games_per_worker)
        self.simulations      = int(simulations)
        self.device           = device or C.torch_device()
<<<<<<< HEAD

        self.buffer = PrioritizedReplayBuffer()
        if (C.REPLAY_DIR / "buffer.npz").exists():
            try:
                self.buffer.load(C.REPLAY_DIR / "buffer.npz")
=======
        self.heartbeat_period = float(heartbeat_period)

        self.buffer = PrioritizedReplayBuffer()

        # 1) Self-play buffer (destructive load — primary source).
        if _SELFPLAY_BUFFER_PATH.exists():
            try:
                self.buffer.load(_SELFPLAY_BUFFER_PATH)
>>>>>>> 05d15f7 (updated npc ai)
                log.info("Replay buffer loaded: %d samples", len(self.buffer))
            except Exception:
                log.exception("Failed to load replay buffer (continuing fresh)")

<<<<<<< HEAD
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
=======
        # 2) Discord live buffer (merged non-destructively on top).
        live_merged = _merge_buffer_from_disk(self.buffer, _LIVE_BUFFER_PATH)
        if live_merged > 0:
            log.info("Discord live buffer merged in: +%d samples "
                     "(total now %d)", live_merged, len(self.buffer))
        # Track how many samples we've already pulled from the live file
        # so the periodic poller only ingests newly-added ones. We use
        # the file size as a cheap "did anything change?" signal.
        try:
            self._live_buffer_mtime = (_LIVE_BUFFER_PATH.stat().st_mtime
                                       if _LIVE_BUFFER_PATH.exists() else 0.0)
        except Exception:
            self._live_buffer_mtime = 0.0

        self.trainer = Trainer(self.buffer, device=self.device)

        self.request_q = Queue(maxsize=4096)
        self.sample_q  = Queue(maxsize=2048)
        self.response_qs: list[Queue] = [Queue(maxsize=4) for _ in range(self.workers)]
        self.worker_stats: list[WorkerStats] = [WorkerStats() for _ in range(self.workers)]
        self._procs: list[Process] = []
        self._stop = threading.Event()

        self._inference_server: Optional[BatchedInferenceServer] = None
        self._inference_thread: Optional[threading.Thread] = None
        self._inference_restarts = 0

        self._batches_drained = 0
        self._samples_drained = 0
        self._live_buffer_ingested = live_merged

    # ------------------------------------------------------------------
    def _build_inference_server(self) -> BatchedInferenceServer:
        batch_size = max(4, self.workers)
        return BatchedInferenceServer(
            self.trainer.net,
            self.request_q,
            {wid: q for wid, q in enumerate(self.response_qs)},
            batch_size=batch_size,
            max_wait_ms=1.0,
            device=self.device,
        )

    def _start_inference_server(self) -> None:
        self._inference_server = self._build_inference_server()
        t = threading.Thread(target=self._inference_server.serve_forever,
                             daemon=True, name="inference-server")
        t.start()
        self._inference_thread = t
        log.info("Inference server started (batch_size=%d, max_wait=1ms)",
                 self._inference_server.batch)

    def _inference_watchdog(self) -> None:
        while not self._stop.is_set():
            time.sleep(1.0)
            t = self._inference_thread
            if t is None:
                continue
            if not t.is_alive():
                self._inference_restarts += 1
                log.error("inference-server thread died (restart #%d) — respawning",
                          self._inference_restarts)
                try:
                    if self._inference_server is not None:
                        self._inference_server.stop()
                except Exception:
                    pass
                self._start_inference_server()

    # ------------------------------------------------------------------
    def _live_buffer_poll_loop(self) -> None:
        """Watch ``live_buffer.npz`` and merge in any newly-played games
        from the Discord bot. Polls every ``_LIVE_BUFFER_POLL_S`` seconds.
        """
        while not self._stop.is_set():
            time.sleep(_LIVE_BUFFER_POLL_S)
            try:
                if not _LIVE_BUFFER_PATH.exists():
                    continue
                mtime = _LIVE_BUFFER_PATH.stat().st_mtime
                if mtime <= self._live_buffer_mtime:
                    continue
                # The Discord bot keeps the file as a *cumulative* dump,
                # so naive re-merge would double-count. We snapshot the
                # current size first, then read, then push only the
                # *tail* (samples beyond what we previously ingested).
                data = np.load(_LIVE_BUFFER_PATH, allow_pickle=False)
                n = int(data["size"])
                start = self._live_buffer_ingested
                if n <= start:
                    self._live_buffer_mtime = mtime
                    continue
                states   = data["states"][start:n]
                policies = data["policy"][start:n]
                values   = data["values"][start:n]
                masks    = data["masks"][start:n]
                self.buffer.push_many(states, policies, values, masks)
                added = n - start
                self._live_buffer_ingested = n
                self._live_buffer_mtime = mtime
                log.info("Discord live buffer: +%d new samples merged "
                         "(total ingested from live: %d, buffer size: %d)",
                         added, self._live_buffer_ingested, len(self.buffer))
            except Exception:
                log.exception("live-buffer poll failed")
>>>>>>> 05d15f7 (updated npc ai)

    # ------------------------------------------------------------------
    def _start_workers(self) -> None:
        for wid in range(self.workers):
<<<<<<< HEAD
            rq = self.response_qs[wid]   # already created in __init__
            p = Process(
                target=_worker_main,
                args=(wid, self.request_q, rq, self.sample_q,
                      self._stop, self.games_per_worker, self.simulations),
=======
            rq = self.response_qs[wid]
            p = Process(
                target=_worker_main,
                args=(wid, self.request_q, rq, self.sample_q,
                      self._stop, self.games_per_worker, self.simulations,
                      self.worker_stats[wid]),
>>>>>>> 05d15f7 (updated npc ai)
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
<<<<<<< HEAD
=======
            self._batches_drained += 1
            self._samples_drained += len(states)

    # ------------------------------------------------------------------
    def _heartbeat_loop(self) -> None:
        last_games = 0
        last_sims  = 0
        last_buf   = 0
        last_t     = time.time()
        while not self._stop.is_set():
            time.sleep(self.heartbeat_period)
            now = time.time()
            dt = max(1e-6, now - last_t)

            games_done   = sum(s.games_done.value      for s in self.worker_stats)
            games_crash  = sum(s.games_crashed.value   for s in self.worker_stats)
            games_skip   = sum(s.games_skipped.value   for s in self.worker_stats)
            games_tout   = sum(s.games_timed_out.value for s in self.worker_stats)
            sims_total   = sum(s.sims_total.value      for s in self.worker_stats)
            turns_total  = sum(s.turns_total.value     for s in self.worker_stats)
            alive_count  = sum(int(s.alive.value)      for s in self.worker_stats)

            stuck = []
            for wid, s in enumerate(self.worker_stats):
                if not s.alive.value:
                    continue
                age = now - s.last_heartbeat.value
                if age > 15.0:
                    stuck.append(f"w{wid}:{age:.0f}s")

            buf_size = len(self.buffer)
            req_q_sz = _qsize(self.request_q)
            sam_q_sz = _qsize(self.sample_q)

            gps = (games_done - last_games) / dt
            sps = (sims_total  - last_sims)  / dt
            bps = (buf_size    - last_buf)   / dt

            inf_t = self._inference_thread
            inf_alive = bool(inf_t and inf_t.is_alive())

            log.info(
                "[hb] buf=%d (+%.0f/s) games=%d (+%.2f/s, ✗%d skip%d ⌛%d) "
                "turns=%d sims=%d (%.0f/s) workers=%d/%d alive "
                "inf=%s(r%d) req_q=%d samp_q=%d drained=%d batches/%d samples "
                "live=%d%s",
                buf_size, bps,
                games_done, gps, games_crash, games_skip, games_tout,
                turns_total, sims_total, sps,
                alive_count, self.workers,
                "up" if inf_alive else "DOWN", self._inference_restarts,
                req_q_sz, sam_q_sz,
                self._batches_drained, self._samples_drained,
                self._live_buffer_ingested,
                f" stuck={','.join(stuck)}" if stuck else "",
            )

            last_games, last_sims, last_buf, last_t = games_done, sims_total, buf_size, now
>>>>>>> 05d15f7 (updated npc ai)

    # ------------------------------------------------------------------
    def run(self, max_steps: int = C.OPT_TRAIN_STEPS) -> None:
        self._start_inference_server()
        self._start_workers()
<<<<<<< HEAD
        sample_thread = threading.Thread(target=self._drain_sample_q,
                                         daemon=True, name="sample-drain")
        sample_thread.start()
=======

        threading.Thread(target=self._drain_sample_q,
                         daemon=True, name="sample-drain").start()
        threading.Thread(target=self._heartbeat_loop,
                         daemon=True, name="heartbeat").start()
        threading.Thread(target=self._inference_watchdog,
                         daemon=True, name="inference-watchdog").start()
        threading.Thread(target=self._live_buffer_poll_loop,
                         daemon=True, name="live-buffer-poll").start()
>>>>>>> 05d15f7 (updated npc ai)

        def _on_sigint(signum, frame):
            log.info("SIGINT received – shutting down ...")
            self._stop.set()
<<<<<<< HEAD
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
=======
            if self._inference_server is not None:
                self._inference_server.stop()
            self.sample_q.put(None)
            try:
                self.buffer.save(_SELFPLAY_BUFFER_PATH)
                log.info("Buffer saved on exit (%d samples)", len(self.buffer))
            except Exception:
                log.exception("Buffer save on exit failed")
            sys.exit(0)
        signal.signal(signal.SIGINT, _on_sigint)

        def _autosave():
            while not self._stop.is_set():
                time.sleep(30)
                try:
                    self.buffer.save(_SELFPLAY_BUFFER_PATH)
                    log.info("[autosave] buffer persisted (%d samples)", len(self.buffer))
>>>>>>> 05d15f7 (updated npc ai)
                except Exception:
                    log.exception("buffer autosave failed")
        threading.Thread(target=_autosave, daemon=True, name="buf-autosave").start()

        try:
            self.trainer.run(max_steps)
        finally:
            self._stop.set()
<<<<<<< HEAD
            self._inference_server.stop()
=======
            if self._inference_server is not None:
                self._inference_server.stop()
            try:
                self.buffer.save(_SELFPLAY_BUFFER_PATH)
                log.info("Buffer saved on shutdown (%d samples)", len(self.buffer))
            except Exception:
                log.exception("Buffer save on shutdown failed")
>>>>>>> 05d15f7 (updated npc ai)
            for p in self._procs:
                try:
                    p.terminate()
                except Exception:
                    pass
            try:
<<<<<<< HEAD
                self.buffer.save(C.REPLAY_DIR / "buffer.npz")
=======
                self.buffer.save(_SELFPLAY_BUFFER_PATH)
>>>>>>> 05d15f7 (updated npc ai)
            except Exception:
                log.exception("final buffer save failed")


<<<<<<< HEAD
=======
def _qsize(q) -> int:
    try:
        return q.qsize()
    except (NotImplementedError, Exception):
        return -1


>>>>>>> 05d15f7 (updated npc ai)
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
<<<<<<< HEAD
=======
    ap.add_argument("--heartbeat",        type=float, default=2.0)
>>>>>>> 05d15f7 (updated npc ai)
    ap.add_argument("--run-dir",          type=str, default=None,
                    help="Override DUELER_RUN_DIR (sets where checkpoints land).")
    args = ap.parse_args()

    if args.run_dir:
        os.environ["DUELER_RUN_DIR"] = args.run_dir
<<<<<<< HEAD
        # Re-import config so paths refresh
=======
>>>>>>> 05d15f7 (updated npc ai)
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
<<<<<<< HEAD
=======
        heartbeat_period=args.heartbeat,
>>>>>>> 05d15f7 (updated npc ai)
    )
    dt.run(max_steps=args.steps)


if __name__ == "__main__":
    mp.set_start_method("fork")
    main()


<<<<<<< HEAD
__all__ = ["DistributedTrainer", "main"]
=======
__all__ = ["DistributedTrainer", "main"]
>>>>>>> 05d15f7 (updated npc ai)
