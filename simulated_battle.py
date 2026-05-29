from __future__ import annotations

import argparse
import logging
import random
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from pokemonduel.ai import (
    HeadlessBattle, NPCTeamAI, Trainer,
    initial_send_out, run_turn,
    PrioritizedReplayBuffer,
    TrajectoryBatch, BattleEncoder, HiddenInfoTracker,
    legal_action_mask, action_to_engine, apply_action,
    random_two_teams,
)
from pokemonduel.ai import config as C
from pokemonduel.trainers.npc_trainer import NPCTrainer


def run_battle(seed: Optional[int] = None,
               simulations: int = C.MCTS_SIMULATIONS,
               max_turns: int = C.SELFPLAY_MAX_TURNS,
               verbose: bool = False
               ) -> tuple[int, int, "TrajectoryBatch", "TrajectoryBatch"]:
    """Run a single headless NPC-vs-NPC battle.

    Returns ``(winner_side, turns_played, traj1, traj2)``.
    """
    from pokemonduel.core.registry import load_all
    load_all()
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed & 0xFFFFFFFF)
        torch.manual_seed(seed)

    party1, party2 = random_two_teams(seed=seed)
    t1 = NPCTrainer("NPC Alpha", party1)
    t2 = NPCTrainer("NPC Beta",  party2)
    battle = HeadlessBattle(t1, t2)

    ai1 = NPCTeamAI(t1, t2, simulations=simulations)
    ai2 = NPCTeamAI(t2, t1, simulations=simulations)
    ai1.set_battle(battle); ai2.set_battle(battle)
    t1.set_ai(ai1);          t2.set_ai(ai2)

    try:
        lead1 = ai1.choose_lead()
        if lead1 != 0 and 0 <= lead1 < len(t1.party) and t1.party[lead1].hp > 0:
            t1.switch_poke(lead1)
        lead2 = ai2.choose_lead()
        if lead2 != 0 and 0 <= lead2 < len(t2.party) and t2.party[lead2].hp > 0:
            t2.switch_poke(lead2)
    except Exception:
        logging.exception("choose_lead failed; using default slot 0")

    initial_send_out(battle)
    if verbose:
        print(battle.msg)
        battle.msg = ""

    winner_side = 0
    for turn_idx in range(max_turns):
        if t1.current_pokemon is None and t1.has_alive_pokemon():
            _resolve_forced_switch(t1, t2, battle, ai1)
        if t2.current_pokemon is None and t2.has_alive_pokemon():
            _resolve_forced_switch(t2, t1, battle, ai2)

        if not t1.has_alive_pokemon():
            winner_side = 2
            break
        if not t2.has_alive_pokemon():
            winner_side = 1
            break

        # Ask AIs for their actions. Both calls *mutate* selected_action / should_mega_evolve on their trainer / current Pokémon, matching the live ``NPCTrainer.move`` contract.
        _ai_action(ai1, t1, t2, battle)
        _ai_action(ai2, t2, t1, battle)

        _msg, w = run_turn(battle)
        if verbose:
            print(battle.msg)
            battle.msg = ""
        if w is t1:
            winner_side = 1
            break
        if w is t2:
            winner_side = 2
            break

    if winner_side == 0:
        h1 = sum(max(0, p.hp) for p in t1.party)
        h2 = sum(max(0, p.hp) for p in t2.party)
        winner_side = 1 if h1 > h2 else (2 if h2 > h1 else 0)

    # Notify each AI so it can persist its trajectory into the live buffer.
    try:
        ai1.on_battle_end(winner_side == 1)
        ai2.on_battle_end(winner_side == 2)
    except Exception:
        logging.exception("on_battle_end failed")

    return winner_side, battle.turn, ai1._traj, ai2._traj


def _resolve_forced_switch(trainer, opponent, battle, ai) -> None:
    """Handle a forced switch by asking the AI which party slot to send out."""
    from pokemonduel.moves import Move

    try:
        slot = ai.choose_switch(mid_turn=True)
    except Exception:
        slot = 0
    if not (0 <= slot < len(trainer.party)) or trainer.party[slot].hp <= 0 \
            or trainer.party[slot] is trainer.current_pokemon:
        for i, p in enumerate(trainer.party):
            if p.hp > 0 and p is not trainer.current_pokemon:
                slot = i
                break
    try:
        trainer.switch_poke(slot, mid_turn=True)
        if opponent.current_pokemon is not None:
            battle.msg += trainer.current_pokemon.send_out(opponent.current_pokemon, battle)
    except Exception:
        logging.exception("forced switch failed")


def _ai_action(ai, trainer, opponent, battle) -> None:
    from pokemonduel.moves import Move
    try:
        chosen_move, switch_idx = ai.choose_move()
        if switch_idx is not None:
            trainer.selected_action = switch_idx
        else:
            trainer.selected_action = chosen_move
    except Exception:
        logging.exception("AI action failed; falling back to first legal move")
        trainer.selected_action = Move.struggle()


def main() -> None:
    ap = argparse.ArgumentParser(description="Headless NPC-vs-NPC trainer.")
    ap.add_argument("--battles",     type=int, default=50,
                    help="number of headless battles to play")
    ap.add_argument("--simulations", type=int, default=C.MCTS_SIMULATIONS,
                    help="MCTS simulations per move")
    ap.add_argument("--max-turns",   type=int, default=C.SELFPLAY_MAX_TURNS)
    ap.add_argument("--train",       action="store_true",
                    help="run gradient updates against the live buffer after each batch")
    ap.add_argument("--steps",       type=int, default=2000,
                    help="number of gradient steps when --train is set")
    ap.add_argument("--verbose",     action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    t0 = time.time()
    wins = [0, 0, 0]
    for i in range(args.battles):
        ws, turns, _t1, _t2 = run_battle(seed=random.randint(0, 2**31 - 1),
                                         simulations=args.simulations,
                                         max_turns=args.max_turns,
                                         verbose=args.verbose)
        wins[ws] += 1
        elapsed = time.time() - t0
        bps = (i + 1) / max(1e-6, elapsed)
        print(f"[{i+1:>4}/{args.battles}] winner=s{ws} turns={turns} "
              f"score 1={wins[1]} 2={wins[2]} tie={wins[0]}  "
              f"({bps:.2f} battles/s)")

    if args.train:
        from pokemonduel.ai.npc_bridge import _ensure_buffer
        buf = _ensure_buffer()
        trainer = Trainer(buf)
        trainer.run(max_steps=trainer.step + args.steps,
                    min_buffer=max(1024, len(buf) // 4))

    total = sum(wins)
    print(f"\nFinal score:  side1 = {wins[1]} ({wins[1]/total:.1%}),  "
          f"side2 = {wins[2]} ({wins[2]/total:.1%}),  ties = {wins[0]}")


if __name__ == "__main__":
    main()
