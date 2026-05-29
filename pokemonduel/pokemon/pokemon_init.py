from ..data_gen import find, find_one
from ..misc import NonVolatileEffect, Metronome, ExpiringEffect, ExpiringItem, HeldItem


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
        self.nature = kwargs['nature']
        self.moves = kwargs['moves']
        self.ability_id = kwargs['ability_id']
        self.mega_ability_id = kwargs['mega_ability_id']
        self.type_ids = kwargs['type_ids']
        self.mega_type_ids = kwargs['mega_type_ids']
        self._starting_name = self._name
        self.starting_hp = self.hp
        self.starting_hpiv = self.hpiv
        self.starting_atkiv = self.atkiv
        self.starting_defiv = self.defiv
        self.starting_spatkiv = self.spatkiv
        self.starting_spdefiv = self.spdefiv
        self.starting_speediv = self.speediv
        self.starting_hpev = self.hpev
        self.starting_atkev = self.atkev
        self.starting_defev = self.defev
        self.starting_spatkev = self.spatkev
        self.starting_spdefev = self.spdefev
        self.starting_speedev = self.speedev
        self.starting_moves = self.moves.copy()
        self.starting_ability_id = self.ability_id
        self.starting_type_ids = self.type_ids.copy()
        self.starting_weight = max(1, kwargs['weight'])
        self.attack_stage = 0
        self.defense_stage = 0
        self.spatk_stage = 0
        self.spdef_stage = 0
        self.speed_stage = 0
        self.accuracy_stage = 0
        self.evasion_stage = 0
        self.level = kwargs['level']
        self.shiny = kwargs['shiny']
        self.radiant = kwargs['radiant']
        self.skin = kwargs['skin']
        self.id = kwargs['id']
        self.held_item = HeldItem(kwargs['held_item'], self)
        self.happiness = kwargs['happiness']
        self.gender = kwargs['gender']
        self.can_still_evolve = kwargs['can_still_evolve']
        self.disliked_flavor = kwargs['disliked_flavor']

        self.owner = None
        self.active_turns = 0

        self.cursed = False
        self.switched = False
        self.minimized = False
        self.nv = NonVolatileEffect(self)
        self.metronome = Metronome()
        self.leech_seed = False
        self.stockpile = 0
        self.flinched = False
        self.confusion = ExpiringEffect(0)

        self.can_move = True
        self.has_moved = False
        # Boolean - stores whether this poke swapped in this turn, and should not have the next_turn function be called.
        self.swapped_in = False
        self.ever_sent_out = False
        # Boolean - stores whether this poke should attempt to mega evolve this turn.
        self.should_mega_evolve = False

        self.last_move = None
        self.last_move_damage = None
        self.last_move_failed = False
        self.locked_move = None
        self.choice_move = None
        self.disable = ExpiringItem()
        self.taunt = ExpiringEffect(0)
        self.encore = ExpiringItem()
        self.torment = False
        self.imprison = False
        self.heal_block = ExpiringEffect(0)
        self.bide = None
        self.focus_energy = False
        self.perish_song = ExpiringEffect(0)
        self.nightmare = False
        self.defense_curl = False
        self.fury_cutter = 0
        self.bind = ExpiringEffect(0)
        self.substitute = 0
        self.silenced = ExpiringEffect(0)
        self.rage = False
        self.mind_reader = ExpiringItem()
        self.destiny_bond = False
        # ExpiringEffect - stores whether destiny bond is on cooldown and cannot be executed.
        self.destiny_bond_cooldown = ExpiringEffect(0)
        # Boolean - stores whether or not this poke is prevented from switching out. This does not prevent moves that swap the target or user.
        self.trapping = False
        # Boolean - stores whether or not this poke is under the effect of ingrain. This does not prevent moves that swap the user, but does prevent target swaps.
        self.ingrain = False
        self.infatuated = None
        self.aqua_ring = False
        self.magnet_rise = ExpiringEffect(0)
        self.dive = False
        self.dig = False
        self.fly = False
        # Boolean - stores whether or not this poke is in a semi-invulnerable state from shadow force or phantom force.
        self.shadow_force = False
        # ExpiringEffect - stores how long this poke cannot be hit by critical hits due to lucky chant.
        self.lucky_chant = ExpiringEffect(0)
        self.grounded_by_move = False
        self.charge = ExpiringEffect(0)
        # ExpiringEffect - stores the number of turns pokes cannot fall asleep.
        self.uproar = ExpiringEffect(0)
        self.magic_coat = False
        self.power_trick = False
        self.power_shift = False
        self.yawn = ExpiringEffect(0)
        self.ion_deluge = False
        self.electrify = False
        self.protection_used = False
        self.protection_chance = 1
        self.protect = False
        self.endure = False
        self.wide_guard = False
        self.crafty_shield = False
        self.king_shield = False
        self.spiky_shield = False
        self.mat_block = False
        self.baneful_bunker = False
        self.quick_guard = False
        self.obstruct = False
        self.silk_trap = False
        self.burning_bulwark = False
        self.laser_focus = ExpiringEffect(0)
        self.powdered = False
        self.snatching = False
        self.telekinesis = ExpiringEffect(0)
        self.embargo = ExpiringEffect(0)
        self.echoed_voice_power = 40
        self.echoed_voice_used = False
        self.curse = False
        self.fairy_lock = ExpiringEffect(0)
        self.grudge = False
        self.foresight = False
        self.miracle_eye = False
        self.beak_blast = False
        self.no_retreat = False
        self.dmg_this_turn = False
        self.ate_berry = False
        self.corrosive_gas = False
        self.stat_increased = False
        self.stat_decreased = False
        self.roost = False
        self.octolock = False
        self.attack_split = None
        self.spatk_split = None
        self.defense_split = None
        self.spdef_split = None
        self.autotomize = 0
        self.lansat_berry_ate = False
        self.micle_berry_ate = False
        self.tar_shot = False
        # ExpiringEffect - stores the number of turns this pokemon is lowering the opponent's speed at the end of every turn.
        self.syrup_bomb = ExpiringEffect(0)
        # Int - stores the number of times this pokemon has been hit this battle, and does NOT reset when switching out.
        self.num_hits = 0

        self.flash_fire = False
        self.truant_turn = 0
        self.ice_repaired = False
        self.last_berry = None
        self.cud_chew = ExpiringEffect(0)
        self.booster_energy = False
        self.supersweet_syrup = False

    def pretty_name(self):
        return self.name.replace("-", " ").title()

    def has_move(self, movename):
        for move in self.moves:
            if movename.lower() in move.name.lower():
                return True
        return False
