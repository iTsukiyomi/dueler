"""
ai/checkpoint.py — Resumable checkpoint management.

A checkpoint bundles:

* network weights (state-dict)
* optimiser state
* LR-scheduler state
* training step counter
* the buffer file path (the buffer itself is stored separately because
  it can be huge — see ``replay_buffer.py:save``)
* RNG state (numpy + torch) for deterministic resume
* ELO snapshot
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch

from . import config as C


# ─────────────────────────────────────────────────────────────────────────────
def save_checkpoint(path: str | Path,
                    network: torch.nn.Module,
                    optimizer: Optional[torch.optim.Optimizer] = None,
                    scheduler=None,
                    *,
                    step: int = 0,
                    extra: Optional[Dict[str, Any]] = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "step":           int(step),
        "network":        network.state_dict(),
        "optimizer":      optimizer.state_dict() if optimizer is not None else None,
        "scheduler":      scheduler.state_dict() if scheduler is not None else None,
        "rng":            {
            "numpy":  np.random.get_state(),
            "torch":  torch.get_rng_state(),
            "cuda":   torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        },
        "saved_at":       time.time(),
        "extra":          extra or {},
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, tmp)
    os.replace(tmp, path)


# ─────────────────────────────────────────────────────────────────────────────
def load_checkpoint(path: str | Path,
                    network: torch.nn.Module,
                    optimizer: Optional[torch.optim.Optimizer] = None,
                    scheduler=None,
                    *,
                    map_location: Optional[torch.device] = None,
                    strict: bool = True) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"step": 0, "extra": {}}
    payload = torch.load(path, map_location=map_location or "cpu", weights_only=False)
    network.load_state_dict(payload["network"], strict=strict)
    if optimizer is not None and payload.get("optimizer") is not None:
        optimizer.load_state_dict(payload["optimizer"])
    if scheduler is not None and payload.get("scheduler") is not None:
        scheduler.load_state_dict(payload["scheduler"])
    rng = payload.get("rng") or {}
    try:
        if rng.get("numpy") is not None:
            np.random.set_state(rng["numpy"])
        if rng.get("torch") is not None:
            torch.set_rng_state(rng["torch"])
        if rng.get("cuda") is not None and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(rng["cuda"])
    except Exception:
        pass
    return {
        "step":     int(payload.get("step", 0)),
        "saved_at": payload.get("saved_at"),
        "extra":    payload.get("extra", {}),
    }


# ─────────────────────────────────────────────────────────────────────────────
def export_torchscript(network: torch.nn.Module, path: str | Path,
                       example_dim: int) -> None:
    """Trace the network with TorchScript for blazing-fast inference."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    network.eval()
    dummy = torch.zeros(2, example_dim, dtype=torch.float32,
                        device=next(network.parameters()).device)
    traced = torch.jit.trace(network, dummy)
    traced.save(str(path))


# ─────────────────────────────────────────────────────────────────────────────
def write_meta(meta_path: str | Path, meta: Dict[str, Any]) -> None:
    meta_path = Path(meta_path)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)


def read_meta(meta_path: str | Path) -> Dict[str, Any]:
    meta_path = Path(meta_path)
    if not meta_path.exists():
        return {}
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = [
    "save_checkpoint",
    "load_checkpoint",
    "export_torchscript",
    "write_meta",
    "read_meta",
]
