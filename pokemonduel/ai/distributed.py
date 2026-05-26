"""
ai/distributed.py — Multiprocessing self-play coordinator.

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
"""
from __future__ import annotations

import argparse
import logging
from multiprocessing import Process, Queue, Value
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


                 simulations: int,
                 stats: WorkerStats) -> None:
    logging.basicConfig(level=logging.INFO,
                        format=f"%(asctime)s [w{worker_id}] %(message)s")
    log.info("worker %d up", worker_id)
    np.random.seed(os.getpid() ^ int(time.time()))
    client = RemoteInferenceClient(request_q, response_q, worker_id)

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
        if traj1.size:
            sample_q.put(traj1.finalise(+1 if winner == 1 else (-1 if winner == 2 else 0)))
        if traj2.size:
            sample_q.put(traj2.finalise(+1 if winner == 2 else (-1 if winner == 1 else 0)))
        n_done += 1

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


# ─────────────────────────────────────────────────────────────────────────────
# Coordinator
# ─────────────────────────────────────────────────────────────────────────────
class DistributedTrainer:
    def __init__(self,
                 *,
                 workers: int = C.SELFPLAY_WORKERS,
                 games_per_worker: int = C.SELFPLAY_BATTLES_PER_W,
                 simulations: int = C.MCTS_SIMULATIONS,
                 device: Optional[torch.device] = None,
                 heartbeat_period: float = 2.0) -> None:
        self.workers          = max(1, int(workers))
        self.games_per_worker = int(games_per_worker)
        self.simulations      = int(simulations)
        self.device           = device or C.torch_device()
        self.heartbeat_period = float(heartbeat_period)

        self.buffer = PrioritizedReplayBuffer()

        # 1) Self-play buffer (destructive load — primary source).
        if _SELFPLAY_BUFFER_PATH.exists():
            try:
                self.buffer.load(_SELFPLAY_BUFFER_PATH)
                log.info("Replay buffer loaded: %d samples", len(self.buffer))
            except Exception:
                log.exception("Failed to load replay buffer (continuing fresh)")

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

    # ------------------------------------------------------------------
    def _start_workers(self) -> None:
        for wid in range(self.workers):
            rq = self.response_qs[wid]
            p = Process(
                target=_worker_main,
                args=(wid, self.request_q, rq, self.sample_q,
                      self._stop, self.games_per_worker, self.simulations,
                      self.worker_stats[wid]),
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

        threading.Thread(target=self._drain_sample_q,
                         daemon=True, name="sample-drain").start()
        threading.Thread(target=self._heartbeat_loop,
                         daemon=True, name="heartbeat").start()
        threading.Thread(target=self._inference_watchdog,
                         daemon=True, name="inference-watchdog").start()
        threading.Thread(target=self._live_buffer_poll_loop,
                         daemon=True, name="live-buffer-poll").start()

        def _on_sigint(signum, frame):
            log.info("SIGINT received – shutting down ...")
            self._stop.set()
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
                except Exception:
                    log.exception("buffer autosave failed")
        threading.Thread(target=_autosave, daemon=True, name="buf-autosave").start()

        try:
            self.trainer.run(max_steps)
        finally:
            self._stop.set()
            if self._inference_server is not None:
                self._inference_server.stop()
            try:
                self.buffer.save(_SELFPLAY_BUFFER_PATH)
                log.info("Buffer saved on shutdown (%d samples)", len(self.buffer))
            except Exception:
                log.exception("Buffer save on shutdown failed")
            for p in self._procs:
                try:
                    p.terminate()
                except Exception:
                    pass
            try:
                self.buffer.save(_SELFPLAY_BUFFER_PATH)
            except Exception:
                log.exception("final buffer save failed")


    ap.add_argument("--heartbeat",        type=float, default=2.0)
    ap.add_argument("--run-dir",          type=str, default=None,
                    help="Override DUELER_RUN_DIR (sets where checkpoints land).")
    args = ap.parse_args()

    if args.run_dir:
        os.environ["DUELER_RUN_DIR"] = args.run_dir
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
        heartbeat_period=args.heartbeat,
    )
    dt.run(max_steps=args.steps)


if __name__ == "__main__":
    mp.set_start_method("fork")
    main()


__all__ = ["DistributedTrainer", "main"]
