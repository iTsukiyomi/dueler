import random
from ..data_gen import find, find_one
from ..enums import Ability, DamageClass, ElementType
from ..misc import NonVolatileEffect, Metronome, ExpiringEffect, ExpiringItem, HeldItem
from ..moves import Move


class DuelPokemonInit:
    """Pokemon initialization."""

    def __init__(self, **kwargs):
        self.pokemon_id = kwargs['pokemon_id']
        self._name = kwargs['name']
        self._nickname = kwargs['nickname']
        if self._nickname != "None":
            self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
        else:
            self.name = self._name.replace("-", " ")
        self.illusion__name = None
        self.illusion_name = None

        self.base_stats = kwargs['base_stats']
        self.hp = kwargs['hp']
        self.attack = self.base_stats[self._name][1]
        self.defense = self.base_stats[self._name][2]
        self.spatk = self.base_stats[self._name][3]
        self.spdef = self.base_stats[self._name][4]
        self.speed = self.base_stats[self._name][5]
        self.hpiv = min(31, kwargs['hpiv'])
        self.atkiv = min(31, kwargs['atkiv'])
        self.defiv = min(31, kwargs['defiv'])
        self.spatkiv = min(31, kwargs['spatkiv'])
        self.spdefiv = min(31, kwargs['spdefiv'])
        self.speediv = min(31, kwargs['speediv'])
        self.hpev = kwargs['hpev']
        self.atkev = kwargs['atkev']
        self.defev = kwargs['defev']
        self.spatkev = kwargs['spatkev']
        self.spdefev = kwargs['spdefev']
        self.speedev = kwargs['speedev']
        self.nature_stat_deltas = kwargs['nature_stat_deltas']
        self.moves = kwargs['moves']
        self.ability_id = kwargs['ability_id']
        self.mega_ability_id = kwargs['mega_ability_id']
        self.item = kwargs['item']
        self.shiny = kwargs['shiny']
        self.gender = kwargs['gender']
        self.level = kwargs['level']
        self.happiness = kwargs['happiness']
        self.can_still_evolve = kwargs['can_still_evolve']
        self.starting_hp = kwargs['hp']
        self.type_ids = kwargs['type_ids']
        self.starting_type_ids = list(kwargs['type_ids'])

    def pretty_name(self):
        return self.name.replace("-", " ").title()

    def has_move(self, movename):
        for move in self.moves:
            if movename.lower() in move.name.lower():
                return True
        return False