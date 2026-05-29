from __future__ import annotations

import os
from pathlib import Path


AI_DIR        = Path(__file__).resolve().parent
PKG_DIR       = AI_DIR.parent
PROJECT_DIR   = PKG_DIR.parent
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


N_MOVE_ACTIONS   = 4
N_SWITCH_ACTIONS = 6
N_MEGA_ACTIONS   = 4
N_ACTIONS        = N_MOVE_ACTIONS + N_SWITCH_ACTIONS + N_MEGA_ACTIONS
MOVE_OFFSET      = 0
SWITCH_OFFSET    = N_MOVE_ACTIONS
MEGA_OFFSET      = N_MOVE_ACTIONS + N_SWITCH_ACTIONS


MAX_FEATURE_LEN = 4096

NETWORK_HIDDEN     = 768
NETWORK_BLOCKS     = 16
NETWORK_DROPOUT    = 0.0
NETWORK_USE_BN     = True
POLICY_HIDDEN      = 384
VALUE_HIDDEN       = 384


MCTS_SIMULATIONS   = 96
MCTS_EVAL_SIMS     = 32
MCTS_C_PUCT        = 1.8
MCTS_DIRICHLET_A   = 0.30
MCTS_DIRICHLET_E   = 0.25
MCTS_VIRTUAL_LOSS  = 1.0
MCTS_BATCH_SIZE    = 8
MCTS_TEMP_HIGH     = 1.0
MCTS_TEMP_LOW      = 0.05
MCTS_TEMP_DROP_T   = 12
MCTS_MAX_DEPTH     = 4
MCTS_TIME_BUDGET_S = 5.0


SELFPLAY_WORKERS        = max(1, (os.cpu_count() or 4) - 1)
SELFPLAY_BATTLES_PER_W  = 10_000
SELFPLAY_MAX_TURNS      = 120
SELFPLAY_GAME_TIMEOUT_S = 90.0  # Wall-clock timeout per game.
SELFPLAY_RESIGN_TURNS   = 200


REPLAY_CAPACITY    = 500_000
REPLAY_MIN_SIZE    = 2_048
REPLAY_ALPHA       = 0.6
REPLAY_BETA_START  = 0.4
REPLAY_BETA_END    = 1.0
REPLAY_BETA_STEPS  = 200_000
REPLAY_EPS         = 1e-6


OPT_BATCH_SIZE     = 256
OPT_LR             = 1e-3
OPT_LR_MIN         = 1e-5
OPT_WEIGHT_DECAY   = 1e-4
OPT_GRAD_CLIP      = 1.0
OPT_TRAIN_STEPS    = 1_000_000
OPT_SAVE_EVERY     = 10
OPT_EVAL_EVERY     = 500
OPT_LOG_EVERY      = 50
OPT_MIXED_PREC     = True  # Set False to force fp32.
OPT_WARMUP_STEPS   = 1_000
OPT_COSINE_PERIOD  = 50_000
OPT_MIN_BUFFER     = REPLAY_MIN_SIZE
OPT_POLICY_COEF    = 1.0
OPT_VALUE_COEF     = 1.0
OPT_ENTROPY_COEF   = 0.01
LIVE_BUFFER_POLL_S = 30.0  # Seconds between live-buffer file checks.


EVAL_MATCHES       = 10
EVAL_PROMOTE_WR    = 0.55
ELO_K              = 16.0
ELO_INIT           = 1200.0


def torch_device():
    import torch
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
