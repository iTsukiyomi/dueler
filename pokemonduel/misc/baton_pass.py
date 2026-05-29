from ..enums import Ability


class BatonPass():
    """Stores the necessary data from a pokemon to baton pass to another pokemon."""

    def __init__(self, poke):
        self.attack_stage = poke.attack_stage
        self.defense_stage = poke.defense_stage
        self.spatk_stage = poke.spatk_stage
        self.spdef_stage = poke.spdef_stage
        self.speed_stage = poke.speed_stage
        self.evasion_stage = poke.evasion_stage
        self.accuracy_stage = poke.accuracy_stage
        self.confusion = poke.confusion
        self.focus_energy = poke.focus_energy
        self.mind_reader = poke.mind_reader
        self.leech_seed = poke.leech_seed
        self.curse = poke.curse
        self.substitute = poke.substitute
        self.ingrain = poke.ingrain
        self.power_trick = poke.power_trick
        self.power_shift = poke.power_shift
        self.heal_block = poke.heal_block
        self.embargo = poke.embargo
        self.perish_song = poke.perish_song
        self.magnet_rise = poke.magnet_rise
        self.aqua_ring = poke.aqua_ring
        self.telekinesis = poke.telekinesis

    def apply(self, poke):
        """Push this objects data to a poke."""
        if poke.ability() != Ability.CURIOUS_MEDICINE:
            poke.attack_stage = self.attack_stage
            poke.defense_stage = self.defense_stage
            poke.spatk_stage = self.spatk_stage
            poke.spdef_stage = self.spdef_stage
            poke.speed_stage = self.speed_stage
            poke.evasion_stage = self.evasion_stage
            poke.accuracy_stage = self.accuracy_stage
        poke.confusion = self.confusion
        poke.focus_energy = self.focus_energy
        poke.mind_reader = self.mind_reader
        poke.leech_seed = self.leech_seed
        poke.curse = self
        poke.substitute = self.substitute
        poke.ingrain = self.ingrain
        poke.power_trick = self.power_trick
        poke.power_shift = self.power_shift
        poke.heal_block = self.heal_block
        poke.embargo = self.embargo
        poke.perish_song = self.perish_song
        poke.magnet_rise = self.magnet_rise
        poke.aqua_ring = self.aqua_ring
        poke.telekinesis = self.telekinesis
