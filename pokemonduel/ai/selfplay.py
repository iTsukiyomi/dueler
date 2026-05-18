"""
ai/selfplay.py — Generate one AlphaZero self-play game.

A self-play game pits two copies of the *same* network against each other.
At every action point we run an MCTS search, store the resulting visit
distribution as the policy target, sample the played action from the
post-temperature distribution, and step the engine forward via the
headless ``run_turn``.

When the game ends we attach a value target to every recorded transition
(+1 from the eventual winner's perspective, -1 from the loser's). The
result is a ``TrajectoryBatch`` ready to be pushed into the replay buffer.

The function ``play_one_game`` is the unit of work used by the distributed
self-play runner.
"""
from __future__ import annotations

import random
from typing import Optional, Tuple

import numpy as np

from . import config as C
from .action_mask import legal_action_mask, apply_action
from .encoder import BattleEncoder
from .hidden_info import HiddenInfoTracker
from .mcts import MCTS
from .replay_buffer import TrajectoryBatch
from .simulator import HeadlessBattle, initial_send_out, run_turn
from .team_loader import random_two_teams
from ..trainers.npc_trainer import NPCTrainer


# ─────────────────────────────────────────────────────────────────────────────
def _temperature_for_turn(turn: int) -> float:
    return C.MCTS_TEMP_HIGH if turn < C.MCTS_TEMP_DROP_T else C.MCTS_TEMP_LOW


# ─────────────────────────────────────────────────────────────────────────────
def play_one_game(inference,
                  *,
                  seed: Optional[int] = None,
                  simulations: int = C.MCTS_SIMULATIONS,
                  max_turns: int = C.SELFPLAY_MAX_TURNS,
                  verbose: bool = False
                  ) -> Tuple[TrajectoryBatch, TrajectoryBatch, int]:
    """Play one full self-play game.

    Returns ``(traj1, traj2, winner_side)`` where ``winner_side`` is
    ``1``, ``2`` or ``0`` for a draw.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed & 0xFFFFFFFF)

    party1, party2 = random_two_teams(seed=seed)
    t1 = NPCTrainer("AZ_1", party1)
    t2 = NPCTrainer("AZ_2", party2)
    battle = HeadlessBattle(t1, t2)

    # Choose leads (the slot 0 of each party already serves as initial active).
    initial_send_out(battle)

    encoder1 = BattleEncoder(HiddenInfoTracker())
    encoder2 = BattleEncoder(HiddenInfoTracker())
    mcts1 = MCTS(inference, simulations=simulations, encoder=encoder1)
    mcts2 = MCTS(inference, simulations=simulations, encoder=encoder2)

    traj1 = TrajectoryBatch()
    traj2 = TrajectoryBatch()

    winner = None
    resign_streak1 = 0
    resign_streak2 = 0

    for _ in range(max_turns):
        # Either side may need a forced switch (active fainted last turn).
        if t1.current_pokemon is None or t2.current_pokemon is None:
            if t1.current_pokemon is None and t1.has_alive_pokemon():
                _force_switch(t1, t2, battle, mcts1, encoder1, traj1, side=1)
            if t2.current_pokemon is None and t2.has_alive_pokemon():
                _force_switch(t2, t1, battle, mcts2, encoder2, traj2, side=2)

        if not t1.has_alive_pokemon():
            winner = 2
            break
        if not t2.has_alive_pokemon():
            winner = 1
            break

        # ── side 1 search ──
        state1 = encoder1.encode(battle, t1, t2)
        mask1  = legal_action_mask(battle, t1, t2)
        temp   = _temperature_for_turn(battle.turn)
        pol1, act1 = mcts1.search(battle, our_side=1, temperature=temp)
        traj1.add(state1, pol1, mask1, to_play=1)
        apply_action(act1, t1, t2, battle)

        # ── side 2 search ──
        state2 = encoder2.encode(battle, t2, t1)
        mask2  = legal_action_mask(battle, t2, t1)
        pol2, act2 = mcts2.search(battle, our_side=2, temperature=temp)
        traj2.add(state2, pol2, mask2, to_play=2)
        apply_action(act2, t2, t1, battle)

        # ── resign heuristic ──
        v1 = float(np.dot(pol1, np.linspace(-1, 1, C.N_ACTIONS, dtype=np.float32))) * 0
        # use the running root value instead — we don't expose it, so use HP swing
        if t1.current_pokemon and t2.current_pokemon:
            hp_share = sum(max(0, p.hp) for p in t1.party) / max(
                1, sum(max(0, p.hp) for p in t1.party) + sum(max(0, p.hp) for p in t2.party)
            )
            if hp_share < 0.05:
                resign_streak1 += 1
            else:
                resign_streak1 = 0
            if hp_share > 0.95:
                resign_streak2 += 1
            else:
                resign_streak2 = 0
            if resign_streak1 >= C.SELFPLAY_RESIGN_TURNS:
                winner = 2
                break
            if resign_streak2 >= C.SELFPLAY_RESIGN_TURNS:
                winner = 1
                break

        # ── step engine ──
        _msg, w = run_turn(battle)
        if w is not None:
            winner = 1 if w is t1 else (2 if w is t2 else 0)
            break

    if winner is None:
        # Time-out: side with more total HP wins.
        h1 = sum(max(0, p.hp) for p in t1.party)
        h2 = sum(max(0, p.hp) for p in t2.party)
        winner = 1 if h1 > h2 else (2 if h2 > h1 else 0)

    if verbose:
        print(f"[selfplay] winner={winner} turns={battle.turn}")
    return traj1, traj2, winner


# ─────────────────────────────────────────────────────────────────────────────
def _force_switch(trainer, opponent, battle, mcts, encoder, traj, side: int) -> None:
    """Handle a forced switch (active fainted)."""
    state = encoder.encode(battle, trainer, opponent)
    mask  = legal_action_mask(battle, trainer, opponent)
    pol, act = mcts.search(battle, our_side=side, temperature=C.MCTS_TEMP_LOW)
    traj.add(state, pol, mask, to_play=side)
    apply_action(act, trainer, opponent, battle)
    # Apply the switch immediately (the engine normally does it inside
    # ``run_turn`` but a forced switch must resolve before the turn even
    # starts).
    if isinstance(trainer.selected_action, int):
        slot = trainer.selected_action
        # Validate the chosen slot before switching: action masks can become
        # stale when ``valid_swaps`` strips ``last_idx`` from its results,
        # leaving slot 0 as the only "legal" choice even when slot 0 is the
        # just-fainted active.
        target = trainer.party[slot] if 0 <= slot < len(trainer.party) else None
        if target is None or getattr(target, "hp", 0) <= 0:
            slot = next((i for i, p in enumerate(trainer.party) if p.hp > 0), None)
        if slot is not None:
            try:
                trainer.switch_poke(slot)
                opp_active = opponent.current_pokemon
                if opp_active is not None:
                    battle.msg += trainer.current_pokemon.send_out(opp_active, battle)
            except Exception:
                pass
        trainer.selected_action = None


__all__ = ["play_one_game"]
