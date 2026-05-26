"""
ai/trainer.py — Training loop for the policy/value network.

Pulls samples from a ``PrioritizedReplayBuffer`` (filled by self-play
workers), runs cross-entropy/MSE loss, applies gradient clipping, steps a
cosine-annealing scheduler with warm-up, periodically saves checkpoints and
runs evaluation matches against the current best network.

Exposes :class:`Trainer` which is meant to be instantiated *once* per
training run and driven by ``run(num_steps)``.
"""
from __future__ import annotations

import copy
import logging
import math
import os
import shutil
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as Fnn

try:
    from torch.utils.tensorboard import SummaryWriter   # type: ignore
    _HAS_TB = True
except Exception:                                        # pragma: no cover
    SummaryWriter = None
    _HAS_TB = False

from . import config as C
from . import features as F
from .checkpoint import (load_checkpoint, save_checkpoint,
                         write_meta, read_meta)
from .evaluation import EloState, evaluate
from .inference import InferenceEngine
from .network import PokemonAlphaZeroNet
from .replay_buffer import PrioritizedReplayBuffer

log = logging.getLogger("dueler.ai.trainer")


# ─────────────────────────────────────────────────────────────────────────────
# Cosine schedule with linear warm-up
# ─────────────────────────────────────────────────────────────────────────────
class WarmupCosine(torch.optim.lr_scheduler._LRScheduler):
    def __init__(self, optimizer, warmup_steps: int, period: int,
                 lr_min_ratio: float = 0.05, last_epoch: int = -1):
        self.warmup = max(1, warmup_steps)
        self.period = max(1, period)
        self.lr_min_ratio = float(lr_min_ratio)
        super().__init__(optimizer, last_epoch)

    def get_lr(self):
        step = max(1, self.last_epoch)
        warm = self.warmup
        if step < warm:
            scale = step / warm
        else:
            phase = ((step - warm) % self.period) / self.period
            scale = self.lr_min_ratio + (1.0 - self.lr_min_ratio) * 0.5 * (1 + math.cos(math.pi * phase))
        return [base_lr * scale for base_lr in self.base_lrs]


# ─────────────────────────────────────────────────────────────────────────────
# Trainer
# ─────────────────────────────────────────────────────────────────────────────
class Trainer:
    def __init__(self,
                 buffer: PrioritizedReplayBuffer,
                 *,
                 device: Optional[torch.device] = None,
                 ckpt_dir: Path = C.CKPT_DIR,
                 best_path: Path = C.BEST_MODEL,
                 latest_path: Path = C.LATEST_MODEL,
                 tb_dir: Path = C.TB_DIR,
                 elo_path: Path = C.ELO_PATH,
                 meta_path: Path = C.META_PATH) -> None:
        self.buffer    = buffer
        self.device    = device or C.torch_device()
        self.ckpt_dir  = Path(ckpt_dir)
        self.best_path = Path(best_path)
        self.latest_path = Path(latest_path)
        self.tb_dir    = Path(tb_dir)
        self.elo_path  = Path(elo_path)
        self.meta_path = Path(meta_path)

        # ── networks ──
        self.net = PokemonAlphaZeroNet().to(self.device)
        self.best_net = PokemonAlphaZeroNet().to(self.device)
        self.best_net.load_state_dict(self.net.state_dict())

        # ── optimiser / scheduler ──
        self.optimizer = torch.optim.AdamW(
            self.net.parameters(),
            lr=C.OPT_LR,
            weight_decay=C.OPT_WEIGHT_DECAY,
        )
        self.scheduler = WarmupCosine(
            self.optimizer,
            warmup_steps=C.OPT_WARMUP_STEPS,
            period=C.OPT_COSINE_PERIOD,
            lr_min_ratio=max(1e-3, C.OPT_LR_MIN / max(C.OPT_LR, 1e-9)),
        )
        self.scaler = torch.amp.GradScaler(
            self.device.type if self.device.type in ("cuda", "cpu") else "cpu",
            enabled=C.OPT_MIXED_PREC and self.device.type == "cuda",
        )

        # ── elo ──
        self.elo = EloState.load(self.elo_path)

        # ── tensorboard ──
        self.writer = SummaryWriter(str(self.tb_dir)) if _HAS_TB else None

        # ── inference snapshots used by evaluation ──
        self._latest_engine = InferenceEngine(self.net, device=self.device)
        self._best_engine   = InferenceEngine(self.best_net, device=self.device)

        # ── step counter ──
        self.step = 0
        self._maybe_load_latest()

        log.info("Trainer ready on %s. params=%s",
                 self.device, self.net.count_parameters())

    # ------------------------------------------------------------------
    def _maybe_load_latest(self) -> None:
        if self.latest_path.exists():
            info = load_checkpoint(
                self.latest_path, self.net, self.optimizer, self.scheduler,
                map_location=self.device, strict=False,
            )
            self.step = info.get("step", 0)
            log.info("Resumed from step %d", self.step)
        if self.best_path.exists():
            load_checkpoint(self.best_path, self.best_net, map_location=self.device, strict=False)
            log.info("Best network loaded")

    # ------------------------------------------------------------------
    def get_latest_engine(self) -> InferenceEngine:
        return self._latest_engine

    def get_best_engine(self) -> InferenceEngine:
        return self._best_engine

    # ------------------------------------------------------------------
    def train_step(self) -> dict:
        states, policies, values, masks, weights, tree_idxs = \
            self.buffer.sample(C.OPT_BATCH_SIZE)

        x = torch.from_numpy(states).to(self.device, non_blocking=True)
        pi_target = torch.from_numpy(policies).to(self.device, non_blocking=True)
        v_target  = torch.from_numpy(values).to(self.device, non_blocking=True)
        mask = torch.from_numpy(masks).to(self.device, non_blocking=True)
        w = torch.from_numpy(weights).to(self.device, non_blocking=True)

        self.net.train()
        self.optimizer.zero_grad(set_to_none=True)

        with torch.amp.autocast(self.device.type,
                                enabled=(self.scaler.is_enabled())):
            logits, value = self.net(x)
            neg_inf = torch.finfo(logits.dtype).min
            logits = torch.where(mask, logits, torch.full_like(logits, neg_inf))
            log_probs = Fnn.log_softmax(logits, dim=-1)
            # cross-entropy with soft labels π
            policy_loss = -(pi_target * log_probs).sum(dim=-1)
            value_loss  = (v_target - value).pow(2)
            entropy     = -(log_probs.exp() * log_probs).sum(dim=-1)

            per_sample = (
                C.OPT_POLICY_COEF * policy_loss
                + C.OPT_VALUE_COEF * value_loss
                - C.OPT_ENTROPY_COEF * entropy
            )
            loss = (per_sample * w).mean()

        self.scaler.scale(loss).backward()
        self.scaler.unscale_(self.optimizer)
        torch.nn.utils.clip_grad_norm_(self.net.parameters(), C.OPT_GRAD_CLIP)
        self.scaler.step(self.optimizer)
        self.scaler.update()
        self.scheduler.step()

        # Update priorities by value TD error magnitude
        td = (v_target.detach() - value.detach()).abs().cpu().numpy()
        self.buffer.update_priorities(tree_idxs, td)

        self.step += 1
        return {
            "loss":         float(loss.detach().cpu()),
            "policy_loss":  float(policy_loss.mean().detach().cpu()),
            "value_loss":   float(value_loss.mean().detach().cpu()),
            "entropy":      float(entropy.mean().detach().cpu()),
            "lr":           float(self.optimizer.param_groups[0]["lr"]),
            "buffer":       len(self.buffer),
        }

    # ------------------------------------------------------------------
    def maybe_log(self, stats: dict) -> None:
        if self.writer is None or self.step % C.OPT_LOG_EVERY:
            return
        for k, v in stats.items():
            self.writer.add_scalar(f"train/{k}", v, self.step)
        self.writer.flush()

    # ------------------------------------------------------------------
    def save_latest(self) -> None:
        save_checkpoint(
            self.latest_path, self.net, self.optimizer, self.scheduler,
            step=self.step, extra={"params": self.net.count_parameters()},
        )
        write_meta(self.meta_path, {
            "step":   self.step,
            "elo":    self.elo.ratings,
            "params": self.net.count_parameters(),
        })

    def save_best(self) -> None:
        # copy current net to best_net + persist to disk
        self.best_net.load_state_dict(self.net.state_dict())
        save_checkpoint(self.best_path, self.best_net, step=self.step)

    # ------------------------------------------------------------------
    def maybe_evaluate(self, force: bool = False) -> Optional[dict]:
        if not force and (self.step % C.OPT_EVAL_EVERY != 0 or self.step == 0):
            return None
        log.info("Running evaluation at step %d", self.step)
        wr, w, l, d = evaluate(self._latest_engine, self._best_engine,
                               n_matches=C.EVAL_MATCHES)
        log.info("Eval: win=%d loss=%d draw=%d wr=%.3f", w, l, d, wr)
        score_a = (w + 0.5 * d) / max(1, w + l + d)
        self.elo.record_match("latest", "best", score_a)
        self.elo.append_history(self.step)
        self.elo.save(self.elo_path)
        if self.writer is not None:
            self.writer.add_scalar("eval/win_rate",   wr,           self.step)
            self.writer.add_scalar("eval/elo_latest", self.elo.get("latest"), self.step)
            self.writer.add_scalar("eval/elo_best",   self.elo.get("best"),   self.step)

        promoted = False
        if wr >= C.EVAL_PROMOTE_WR:
            self.save_best()
            promoted = True
            log.info("Promoting latest -> best (wr=%.3f)", wr)
        return {"win_rate": wr, "wins": w, "losses": l, "draws": d, "promoted": promoted}

    # ------------------------------------------------------------------
    def run(self, max_steps: int = C.OPT_TRAIN_STEPS, *,
            min_buffer: int = C.OPT_MIN_BUFFER) -> None:
        log.info("Waiting for buffer to fill (>= %d) ...", min_buffer)
        wait_t0  = time.time()
        last_sz  = len(self.buffer)
        last_log = wait_t0
        while len(self.buffer) < min_buffer:
            time.sleep(2.0)
            now  = time.time()
            sz   = len(self.buffer)
            rate = (sz - last_sz) / max(1e-6, now - last_log)
            remaining = max(0, min_buffer - sz)
            eta = (remaining / rate) if rate > 0 else float("inf")
            log.info(
                "[wait] buffer=%d/%d (%.1f%%, +%.1f samples/s, ETA=%s, elapsed=%.0fs)",
                sz, min_buffer,
                100.0 * sz / max(1, min_buffer),
                rate,
                f"{eta:.0f}s" if eta != float("inf") else "?",
                now - wait_t0,
            )
            last_sz, last_log = sz, now
        log.info("Buffer filled to %d samples in %.0fs — starting training for %d steps",
                 len(self.buffer), time.time() - wait_t0, max_steps)
        t0 = time.time()
        last_log_t = t0
        last_log_step = 0
        while self.step < max_steps:
            stats = self.train_step()
            self.maybe_log(stats)
            if self.step % C.OPT_SAVE_EVERY == 0:
                self.save_latest()
            self.maybe_evaluate()
            now = time.time()
            # Log every 200 steps OR every 2 wall-clock seconds (whichever
            # comes first) so progress is visible even when steps are slow.
            if self.step % 200 == 0 or (now - last_log_t) >= 2.0:
                dt_total = now - t0
                rate_overall = self.step / max(1e-6, dt_total)
                rate_recent  = (self.step - last_log_step) / max(1e-6, now - last_log_t)
                log.info("step=%d loss=%.3f pol=%.3f val=%.3f lr=%.2e buf=%d "
                         "(%.2f steps/s, avg=%.2f)",
                         self.step, stats["loss"], stats["policy_loss"],
                         stats["value_loss"], stats["lr"], stats["buffer"],
                         rate_recent, rate_overall)
                last_log_t = now
                last_log_step = self.step
        self.save_latest()
        self.save_best()
        log.info("Training done.")


__all__ = ["Trainer", "WarmupCosine"]
