import random
from ..moves import Move
from .trainer_base import Trainer


class NPCTrainer(Trainer):
    """Represents a pokemon trainer that is a NPC."""

    def __init__(self, party):
        super().__init__("Trainer John", party)

    def move(self, defender, battle):
        """Request a normal move from this trainer AI."""
        status_code, movedata = self.valid_moves(defender)
        if status_code == "forced":
            self.selected_action = movedata
        elif status_code == "struggle":
            self.selected_action = Move.struggle()
        else:
            self.selected_action = self.current_pokemon.moves[random.choice(movedata)]
        self.event.set()

    def swap(self, defender, battle, *, mid_turn=False):
        """Request a swap choice from this trainer AI."""
        poke_idx = random.choice(self.valid_swaps(defender, battle, check_trap=False))
        self.switch_poke(poke_idx, mid_turn=mid_turn)
        self.event.set()

    def is_human(self):
        """Returns True if this trainer is a human player, False if it is an AI."""
        return False