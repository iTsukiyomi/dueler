import random


class Trainer():
    """Base trainer class."""

    def __init__(self, name, party):
        self.name = name
        self.party = party
        self.current_pokemon = None
        self.selected_action = None
        self.event = None
        self.switch_requested = None
        self.switch_target_index = None
        self.mid_turn_remove = False

    def is_human(self):
        return False

    def has_alive_pokemon(self):
        return any(poke.hp > 0 for poke in self.party)

    def get_raw_speed(self):
        if self.current_pokemon is None:
            return 0
        return self.current_pokemon.get_raw_speed()

    def get_battle_speed(self, battle):
        if self.current_pokemon is None:
            return 0
        return self.current_pokemon.get_battle_speed(battle)

    def choose_action(self):
        pass

    def move(self, opponent, battle):
        pass

    def switch(self, index, battle):
        pass

    def __repr__(self):
        return f"<Trainer {self.name}>"