import logging
import random
from ..moves import Move
from .trainer_base import Trainer

log = logging.getLogger("dueler.npc_trainer")


class NPCTrainer(Trainer):
    """
    Represents a pokemon trainer that is a NPC with smart AI.
    """
    def __init__(self, name, party):
        super().__init__(name, party)
        self.ai = None

    def set_ai(self, ai):
        """Set the AI brain for this trainer."""
        self.ai = ai

    def move(self, defender, battle):
        """Request a normal move from this trainer AI."""
        if self.ai:
            self.ai.set_battle(battle)
            chosen_move, switch_idx = self.ai.choose_move()
            if switch_idx is not None:
                # Queue the switch as an integer selected_action so the battle
                # loop handles it at the correct time (same as a human swap).
                # Previously this called self.switch_poke() directly, which
                # both changed current_pokemon before the turn ran (double-action
                # bug) AND left selected_action=None (forfeit bug).
                log.debug(
                    "[NPC %s] move() → queuing switch to slot %d "
                    "(current_pokemon=%s)",
                    self.name, switch_idx,
                    self.current_pokemon.name if self.current_pokemon else "None",
                )
                self.selected_action = switch_idx
            else:
                log.debug(
                    "[NPC %s] move() → selected move %s",
                    self.name,
                    getattr(chosen_move, "name", repr(chosen_move)),
                )
                self.selected_action = chosen_move
        else:
            # Fallback to random if no AI set
            status_code, movedata = self.valid_moves(defender)
            if status_code == "forced":
                self.selected_action = movedata
            elif status_code == "struggle":
                self.selected_action = Move.struggle()
            else:
                # pyrefly: ignore [missing-attribute]
                self.selected_action = self.current_pokemon.moves[random.choice(movedata)]
        self.event.set()

    def swap(self, defender, battle, *, mid_turn=False):
        """Request a swap choice from this trainer AI."""
        if self.ai:
            self.ai.set_battle(battle)
            switch_idx = self.ai.choose_switch(mid_turn=mid_turn)
            if switch_idx is not None:
                self.switch_poke(switch_idx, mid_turn=mid_turn)
            else:
                # Fallback to random
                poke_idx = random.choice(self.valid_swaps(defender, battle, check_trap=False))
                self.switch_poke(poke_idx, mid_turn=mid_turn)
        else:
            # Fallback to random
            poke_idx = random.choice(self.valid_swaps(defender, battle, check_trap=False))
            self.switch_poke(poke_idx, mid_turn=mid_turn)
        self.event.set()

    def is_human(self):
        """Returns True if this trainer is a human player, False if it is an AI."""
        return False
