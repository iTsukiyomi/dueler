"""
ai/config.py — Centralised hyper-parameter and path configuration for the
AlphaZero-style Pokémon battle AI.

All other modules import their constants from here so that we can tune
behaviour in a single place. Values are deliberately conservative for a
laptop / single-GPU box; they scale linearly with hardware.
"""
from __future__ import annotations

import os
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
AI_DIR        = Path(__file__).resolve().parent
PKG_DIR       = AI_DIR.parent                                  # pokemonduel/
PROJECT_DIR   = PKG_DIR.parent                                 # repo root
RUN_DIR       = Path(os.environ.get("DUELER_RUN_DIR",
                                    str(PKG_DIR / "ai_runs" / "default")))
CKPT_DIR      = RUN_DIR / "checkpoints"
REPLAY_DIR    = RUN_DIR / "replays"
LOG_DIR       = RUN_DIR / "logs"
TB_DIR        = RUN_DIR / "tensorboard"
ELO_PATH      = RUN_DIR / "elo.json"
META_PATH     = RUN_DIR / "meta.json"
BEST_MODEL    = CKPT_DIR / "best.pt"
LATEST_MODEL  = CKPT_DIR / "latest.pt"

for _p in (RUN_DIR, CKPT_DIR, REPLAY_DIR, LOG_DIR, TB_DIR):
    _p.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# ACTION SPACE
# ─────────────────────────────────────────────────────────────────────────────
# 0..3   – use move slot 0..3 of the active Pokémon
# 4..9   – switch to party slot 0..5 (the current slot is masked out)
# 10..13 – use move slot 0..3 + mega evolve (only legal if the active poke
#          holds a mega-stone and the team has not yet mega-evolved)
N_MOVE_ACTIONS   = 4
N_SWITCH_ACTIONS = 6
N_MEGA_ACTIONS   = 4
N_ACTIONS        = N_MOVE_ACTIONS + N_SWITCH_ACTIONS + N_MEGA_ACTIONS   # = 14
MOVE_OFFSET      = 0
SWITCH_OFFSET    = N_MOVE_ACTIONS                                # 4
MEGA_OFFSET      = N_MOVE_ACTIONS + N_SWITCH_ACTIONS             # 10


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE / NETWORK SHAPES
# ─────────────────────────────────────────────────────────────────────────────
# The encoder produces a long flat float32 vector. Its exact length is
# computed at import time by ai.features so callers do not need to hard-code
# it; the constant below is a safety upper bound used to pre-allocate
# buffers.
MAX_FEATURE_LEN = 4096

NETWORK_HIDDEN     = 768          # width of every residual block
NETWORK_BLOCKS     = 16           # depth of residual tower
NETWORK_DROPOUT    = 0.0          # disabled by default — AlphaZero rarely needs it
NETWORK_USE_BN     = True
POLICY_HIDDEN      = 384
VALUE_HIDDEN       = 384


# ─────────────────────────────────────────────────────────────────────────────
# MCTS
# ─────────────────────────────────────────────────────────────────────────────
MCTS_SIMULATIONS   = 96           # per move in self-play
MCTS_EVAL_SIMS     = 32          # per move in evaluation / live play
MCTS_C_PUCT        = 1.8
MCTS_DIRICHLET_A   = 0.30         # noise alpha for root exploration
MCTS_DIRICHLET_E   = 0.25         # mixture weight
MCTS_VIRTUAL_LOSS  = 1.0
MCTS_BATCH_SIZE    = 8            # leaf collection batch for batched inference
MCTS_TEMP_HIGH     = 1.0          # turns 1..MCTS_TEMP_DROP_TURN → sample softmax
MCTS_TEMP_LOW      = 0.05         # afterwards → near-greedy
MCTS_TEMP_DROP_T   = 12
MCTS_MAX_DEPTH     = 4            # how many real-engine turns to look ahead
MCTS_TIME_BUDGET_S = 5.0          # wall-clock budget per MCTS search


# ─────────────────────────────────────────────────────────────────────────────
# SELF-PLAY
# ─────────────────────────────────────────────────────────────────────────────
SELFPLAY_WORKERS        = max(1, (os.cpu_count() or 4) - 1)
SELFPLAY_BATTLES_PER_W  = 10_000               # before worker recycles
SELFPLAY_MAX_TURNS      = 120
SELFPLAY_GAME_TIMEOUT_S = 90.0                  # wall-clock timeout per game
SELFPLAY_RESIGN_TURNS   = 200                   # forfeit if game exceeds this


# ─────────────────────────────────────────────────────────────────────────────
# REPLAY BUFFER
# ─────────────────────────────────────────────────────────────────────────────
REPLAY_CAPACITY    = 500_000
REPLAY_MIN_SIZE    = 2_048        # don't train until we have at least this many
REPLAY_ALPHA       = 0.6          # prioritised-experience-replay exponent
REPLAY_BETA_START  = 0.4
REPLAY_BETA_END    = 1.0
REPLAY_BETA_STEPS  = 200_000
REPLAY_EPS         = 1e-6         # small constant to avoid zero priorities


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING / OPTIMISER
# ─────────────────────────────────────────────────────────────────────────────
OPT_BATCH_SIZE     = 256
OPT_LR             = 1e-3
OPT_LR_MIN         = 1e-5
OPT_WEIGHT_DECAY   = 1e-4
OPT_GRAD_CLIP      = 1.0
OPT_TRAIN_STEPS    = 1_000_000
OPT_SAVE_EVERY     = 10
OPT_EVAL_EVERY     = 500
OPT_LOG_EVERY      = 50
OPT_MIXED_PREC     = True         # set False to force fp32
OPT_WARMUP_STEPS   = 1_000
OPT_COSINE_PERIOD  = 50_000       # cosine annealing cycle length
OPT_MIN_BUFFER     = REPLAY_MIN_SIZE
OPT_POLICY_COEF    = 1.0          # loss weight: policy cross-entropy
OPT_VALUE_COEF     = 1.0          # loss weight: value MSE
OPT_ENTROPY_COEF   = 0.01         # loss weight: entropy bonus
LIVE_BUFFER_POLL_S = 30.0         # seconds between live-buffer file checks


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
EVAL_MATCHES       = 10
EVAL_PROMOTE_WR    = 0.55         # candidate must win ≥ 55% to replace best
ELO_K              = 16.0
ELO_INIT           = 1200.0


# ─────────────────────────────────────────────────────────────────────────────
# DEVICE
# ─────────────────────────────────────────────────────────────────────────────
def torch_device():
    import torch
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

