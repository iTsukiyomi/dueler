from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from . import config as C
from .action_mask import action_to_engine, legal_action_mask
from .checkpoint import load_checkpoint
from .encoder import BattleEncoder
from .hidden_info import HiddenInfoTracker
from .inference import InferenceEngine
from .mcts import MCTS
from .network import PokemonAlphaZeroNet
from .replay_buffer import (PrioritizedReplayBuffer,
                            TrajectoryBatch)
from ..moves import Move

log = logging.getLogger("dueler.ai.bridge")


_NETWORK_LOCK   = threading.Lock()
_NETWORK:       Optional[PokemonAlphaZeroNet] = None
_INFERENCE:     Optional[InferenceEngine]     = None
_REPLAY_BUFFER: Optional[PrioritizedReplayBuffer] = None
_BUFFER_PATH    = C.REPLAY_DIR / "live_buffer.npz"


def _ensure_network() -> InferenceEngine:
    """Build (or reload) the singleton network + inference engine."""
    global _NETWORK, _INFERENCE
    with _NETWORK_LOCK:
        if _INFERENCE is not None:
            return _INFERENCE
        device = C.torch_device()
        net = PokemonAlphaZeroNet().to(device)
        for p in (C.BEST_MODEL, C.LATEST_MODEL):
            if Path(p).exists():
                try:
                    load_checkpoint(p, net, map_location=device, strict=False)
                    log.info("Loaded network weights from %s", p)
                    break
                except Exception:
                    log.exception("Failed loading %s; continuing fresh", p)
        else:
            log.warning("No checkpoint found at %s or %s — using a randomly "
                        "initialised network. Train it with "
                        "`python -m pokemonduel.ai.distributed`.",
                        C.BEST_MODEL, C.LATEST_MODEL)
        net.eval()
        _NETWORK = net
        _INFERENCE = InferenceEngine(net, device=device, cache_size=8192)
        return _INFERENCE


def _ensure_buffer() -> PrioritizedReplayBuffer:
    global _REPLAY_BUFFER
    with _NETWORK_LOCK:
        if _REPLAY_BUFFER is None:
            _REPLAY_BUFFER = PrioritizedReplayBuffer(capacity=200_000)
            if _BUFFER_PATH.exists():
                try:
                    _REPLAY_BUFFER.load(_BUFFER_PATH)
                except Exception:
                    log.exception("Failed to load live replay buffer")
        return _REPLAY_BUFFER


def reload_network() -> None:
    """Force the singleton network to reload from disk (for ``;reload``)."""
    global _NETWORK, _INFERENCE
    with _NETWORK_LOCK:
        _NETWORK = None
        _INFERENCE = None


class NPCTeamAI:
    """AlphaZero-backed AI controller for one side of a battle."""

    def __init__(self, trainer, opponent, *, simulations: Optional[int] = None) -> None:
        self.trainer  = trainer
        self.opponent = opponent
        self.battle   = None
        self.simulations = simulations or C.MCTS_SIMULATIONS
        self.engine   = _ensure_network()
        self.encoder  = BattleEncoder(HiddenInfoTracker())
        self.mcts     = MCTS(self.engine,
                             simulations=self.simulations,
                             encoder=self.encoder,
                             add_root_noise=False)
        self._traj    = TrajectoryBatch()
        self._side    = 1

    def set_battle(self, battle) -> None:
        self.battle = battle
        self._side  = 1 if battle.trainer1 is self.trainer else 2

    def _record(self, action: int) -> None:
        try:
            state = self.encoder.encode(self.battle, self.trainer, self.opponent)
            mask  = legal_action_mask(self.battle, self.trainer, self.opponent)
            policy = np.zeros(C.N_ACTIONS, dtype=np.float32)
            policy[action] = 1.0
            self._traj.add(state, policy, mask, to_play=self._side)
        except Exception:
            log.exception("trajectory record failed (ignored)")

    def choose_lead(self) -> int:
        # Search over a 'pseudo-turn' with only switch options legal — the current active is slot 0, search picks the strongest opener.
        if not self.trainer.party:
            return 0
        if self.battle is None:
            return 0
        try:
            _policy, action = self.mcts.search(
                self.battle, our_side=self._side, temperature=0.0)
            # ``action`` from search is a full action index — map switch indices back. Non-switch picks fall through to slot 0.
            if C.SWITCH_OFFSET <= action < C.SWITCH_OFFSET + C.N_SWITCH_ACTIONS:
                return action - C.SWITCH_OFFSET
        except Exception:
            log.exception("choose_lead MCTS failed; defaulting to slot 0")
        return 0

    def choose_move(self):
        """Return ``(move_or_struggle, switch_index_or_None)`` — the
        contract expected by ``NPCTrainer.move``."""
        if self.battle is None or self.trainer.current_pokemon is None:
            return Move.struggle(), None
        try:
            _policy, action = self.mcts.search(
                self.battle, our_side=self._side,
                temperature=C.MCTS_TEMP_LOW)
            self._record(action)
        except Exception:
            log.exception("MCTS failed; falling back to greedy network")
            state = self.encoder.encode(self.battle, self.trainer, self.opponent)
            mask  = legal_action_mask(self.battle, self.trainer, self.opponent)
            policy, _v = self.engine.predict_batch(state[np.newaxis], mask[np.newaxis])
            action = int(np.argmax(policy[0]))

        selected, switch_idx, mega = action_to_engine(
            action, self.trainer, self.opponent, self.battle)
        if mega and self.trainer.current_pokemon is not None:
            self.trainer.current_pokemon.should_mega_evolve = True
        if switch_idx is not None:
            return Move.struggle(), switch_idx
        return selected, None

    def choose_switch(self, mid_turn: bool = False) -> int:
        """Return the party index to switch to."""
        if self.battle is None:
            valid = [i for i, p in enumerate(self.trainer.party) if p.hp > 0]
            return valid[0] if valid else 0
        try:
            _policy, action = self.mcts.search(
                self.battle, our_side=self._side, temperature=C.MCTS_TEMP_LOW)
            self._record(action)
            if C.SWITCH_OFFSET <= action < C.SWITCH_OFFSET + C.N_SWITCH_ACTIONS:
                return action - C.SWITCH_OFFSET
        except Exception:
            log.exception("choose_switch MCTS failed")
        for i, p in enumerate(self.trainer.party):
            if p.hp > 0 and p is not self.trainer.current_pokemon:
                return i
        return 0

    def on_battle_end(self, won: bool) -> None:
        winner_side = +1 if won else -1
        try:
            states, policies, values, masks = self._traj.finalise(winner_side)
            if len(states):
                buf = _ensure_buffer()
                buf.push_many(states, policies, values, masks)
                buf.save(_BUFFER_PATH)
                log.info("Recorded %d transitions from live battle (winner=%s)",
                         len(states), "AI" if won else "OPP")
        except Exception:
            log.exception("Failed to flush live trajectory")


__all__ = ["NPCTeamAI", "reload_network"]
