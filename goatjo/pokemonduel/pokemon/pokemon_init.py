import random
from ..data_gen import find, find_one
from ..enums import Ability, DamageClass, ElementType
from ..misc import NonVolatileEffect, Metronome, ExpiringEffect, ExpiringItem, HeldItem
from ..moves import Move


class DuelPokemonInit:
    """Pokemon initialization."""

    def __init__(self, **kwargs):
        #ID from pfile
        self.pokemon_id = kwargs['pokemon_id']
        self._name = kwargs['name']
        self._nickname = kwargs['nickname']
        if self._nickname != "None":
            self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
        else:
            self.name = self._name.replace("-", " ")
        self.illusion__name = None
        self.illusion_name = None
        
        # Dict {pokname: List[int]}
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
        self.starting_moves = self.moves.copy() #shallow copy to keep the objects but not the list itself
        self.starting_ability_id = self.ability_id
        self.starting_type_ids = self.type_ids.copy()
        #10 "weight" = 1 kg
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
        #Boolean - stores whether this poke swapped in this turn, and should not have the next_turn function be called.
        self.swapped_in = False
        #Boolean - stores whether this poke has ever been sent in.
        self.ever_sent_out = False
        #Boolean - stores whether this poke should attempt to mega evolve this turn.
        self.should_mega_evolve = False
        
        # Moves
        #Optional[Move] - stores the last move used by this poke
        self.last_move = None
        #Optional[Tuple[int, DamageClass]] - stores the damage taken and the class of that damage.
        #Resets at the end of a turn.
        self.last_move_damage = None
        #Boolean - stores whether or not the last move used by this poke failed.
        self.last_move_failed = False
        #Optional[LockedMove] - stores the move this poke is currently locked into using due to it being a multi turn move.
        self.locked_move = None
        #Optional[Move] - stores the move this poke is currently locked into using due to a choice item.
        self.choice_move = None
        #ExpiringItem - stores the number of turns a specific move is disabled.
        self.disable = ExpiringItem()
        #ExpiringEffect - stores the number of turns this poke is taunted.
        self.taunt = ExpiringEffect(0)
        #ExpiringItem - stores the number of turns this poke is giving an encore of a specific move.
        self.encore = ExpiringItem()
        #Boolean - stores whether or not this pokemon is affected by torment.
        self.torment = False
        #Boolean - stores whether or not this pokemon has imprison active.
        self.imprison = False
        #ExpiringEffect - stores the number of turns this poke is blocked from using healing moves.
        self.heal_block = ExpiringEffect(0)
        #Optional[int] - stores the damage takes since bide was started.
        self.bide = None
        #Boolean - stores whether or not this pokemon has used focus energy.
        self.focus_energy = False
        #ExpiringEffect - stores the number of turns until this pokemon faints.
        self.perish_song = ExpiringEffect(0)
        #Boolean - stores whether or not this pokemon is inflicted by nightmare.
        self.nightmare = False
        #Boolean - stores whether or not this pokemon has used defense curl since entering the field.
        self.defense_curl = False
        #Int - stores the number of times fury cutter has been used since entering the field.
        self.fury_cutter = 0
        #ExpiringEffect - stores the number of turns bind is active on this poke.
        self.bind = ExpiringEffect(0)
        #Int - stores the remaining HP of this pokemon's substitute, or 0 if there is no substitute.
        self.substitute = 0
        #ExpiringEffect - stores the number of turns this pokemon is silenced for (can't use sound based moves).
        self.silenced = ExpiringEffect(0)
        #Boolean - stores whether or not this poke is in rage, and gains attack stages after being hit.
        self.rage = False
        #ExpiringItem - stores whether or not mind reader is active ON this poke, and the poke which is reading its mind.
        self.mind_reader = ExpiringItem()
        #Boolean - stores whether any attacker that causes this poke to faint will also faint this turn.
        self.destiny_bond = False
        #ExpiringEffect - stores whether destiny bond is on cooldown and cannot be executed.
        self.destiny_bond_cooldown = ExpiringEffect(0)
        #Boolean - stores whether or not this poke is prevented from switching out. This does not prevent moves that swap the target or user.
        self.trapping = False
        #Boolean - stores whether or not this poke is under the effect of ingrain. This does not prevent moves that swap the user, but does prevent target swaps.
        self.ingrain = False
        #Optional[DuelPokemon] - stores the pokemon that this pokemon is infatuated with.
        self.infatuated = None
        #Boolean - stores whether or not this poke is under the effect of aqua ring.
        self.aqua_ring = False
        #ExpiringEffect - stores the number of turns this pokemon is ungrounded due to magnet rise.
        self.magnet_rise = ExpiringEffect(0)
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from dive.
        self.dive = False
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from dig.
        self.dig = False
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from bounce or fly.
        self.fly = False
        #Boolean - stores whether or not this poke is in a semi-invulnerable state from shadow force or phantom force.
        self.shadow_force = False
        #ExpiringEffect - stores how long this poke cannot be hit by critical hits due to lucky chant.
        self.lucky_chant = ExpiringEffect(0)
        #Boolean - stores whether or not this poke has been hit by smack down or thousand arrows, and is grounded.
        self.grounded_by_move = False
        #ExpiringEffect - stores the number of turns electric type moves have double power from this poke.
        self.charge = ExpiringEffect(0)
        #ExpiringEffect - stores the number of turns pokes cannot fall asleep.
        self.uproar = ExpiringEffect(0)
        #Boolean - stores whether or not this poke reflects status moves due to magic coat.
        self.magic_coat = False
        #Boolean - stores whether or not this poke has used power trick.
        self.power_trick = False
        #Boolean - stores whether or not this poke has used power shift.
        self.power_shift = False
        #ExpiringEffect - stores the number of turns until this poke falls asleep due to drowsiness.
        self.yawn = ExpiringEffect(0)
        #Boolean - stores whether this poke is turning normal moves to electric this turn.
        self.ion_deluge = False
        #Boolean - stores whether this poke's move is changed to electric type due to electrify.
        self.electrify = False
        #Boolean - stores whether this poke used a protection move this turn.
        self.protection_used = False
        #Int - stores the current chance (1/x) that a poke can use a protection move.
        self.protection_chance = 1
        #Boolean - stores whether this poke is protected by protect this turn.
        self.protect = False
        #Boolean - stores whether this poke is protected by endure this turn.
        self.endure = False
        #Boolean - stores whether this poke is protected by wide guard this turn.
        self.wide_guard = False
        #Boolean - stores whether this poke is protected by crafty shield this turn.
        self.crafty_shield = False
        #Boolean - stores whether this poke is protected by king shield this turn.
        self.king_shield = False
        #Boolean - stores whether this poke is protected by spiky shield this turn.
        self.spiky_shield = False
        #Boolean - stores whether this poke is protected by mat block this turn.
        self.mat_block = False
        #Boolean - stores whether this poke is protected by baneful bunker this turn.
        self.baneful_bunker = False
        #Boolean - stores whether this poke is protected by quick guard this turn.
        self.quick_guard = False
        #Boolean - stores whether this poke is protected by obstruct this turn.
        self.obstruct = False
        #Boolean - stores whether this poke is protected by silk trap this turn.
        self.silk_trap = False
        #Boolean - stores whether this poke is protected by burning bulwark this turn.
        self.burning_bulwark = False
        #ExpiringEffect - stores whether this poke will always crit due to laser focus.
        self.laser_focus = ExpiringEffect(0)
        #Boolean - stores whether this poke is coated with powder and will explode if it uses a fire type move.
        self.powdered = False
        #Boolean - stores whether this poke will steal the effect of certain self targeted moves this turn using snatch.
        self.snatching = False
        #ExpiringEffect - stores the number of turns this poke is ungrounded and hits to it never miss due to telekinesis.
        self.telekinesis = ExpiringEffect(0)
        #ExpiringEffect - stores the number of turns this poke is blocked from using held items due to embargo.
        self.embargo = ExpiringEffect(0)
        #Int - stores the current power of echoed voice.
        self.echoed_voice_power = 40
        #Boolean - stores whether echoed voice was used this turn.
        self.echoed_voice_used = False
        #Boolean - stores whether this poke is inflicted with a curse.
        self.curse = False
        #ExpiringEffect - stores whether this poke is preventing swap outs this turn.
        self.fairy_lock = ExpiringEffect(0)
        #Boolean - stores whether this poke remove all PP from a move that kills it this turn.
        self.grudge = False
        #Boolean - stores whether this poke is affected by foresight.
        self.foresight = False
        #Boolean - stores whether this poke is affected by miracle_eye.
        self.miracle_eye = False
        #Boolean - stores whether this poke is currently charging beak blast.
        self.beak_blast = False
        #Boolean - stores whether this poke is unable to switch out from no retreat.
        self.no_retreat = False
        #Boolean - stores whether this poke has taken ANY damage this turn.
        self.dmg_this_turn = False
        #Boolean - stores whether this poke has eaten a berry this battle.
        self.ate_berry = False
        #Boolean - stores whether this poke is unable to use its held item for the rest of the battle due to corrosive gas.
        self.corrosive_gas = False
        #Boolean - stores whether this poke has had a stat increase this turn.
        self.stat_increased = False
        #Boolean - stores whether this poke has had a stat decrease this turn.
        self.stat_decreased = False
        #Boolean - stores whether this poke has had its flying type surpressed this turn.
        self.roost = False
        #Boolean - stores whether this poke is affected by octolock, and has its def/spdef lowered each turn.
        self.octolock = False
        #Optional[Int] - stores the raw attack value this poke's attack is split with.
        self.attack_split = None
        #Optional[Int] - stores the raw special attack value this poke's special attack is split with.
        self.spatk_split = None
        #Optional[Int] - stores the raw defense value this poke's defense is split with.
        self.defense_split = None
        #Optional[Int] - stores the raw special defense value this poke's special defense is split with.
        self.spdef_split = None
        #Int - stores the number of times autotomize has been used since switching out.
        self.autotomize = 0
        #Boolean - stores whether or not this pokemon's critical hit ratio is increased from eating a lansat berry.
        self.lansat_berry_ate = False
        #Boolean - stores whether or not this pokemon's next move has increased accuracy from eating a micle berry.
        self.micle_berry_ate = False
        #Boolean - stores whether or not fire type moves are 2x effective on this pokemon from tar shot.
        self.tar_shot = False
        #ExpiringEffect - stores the number of turns this pokemon is lowering the opponent's speed at the end of every turn.
        self.syrup_bomb = ExpiringEffect(0)
        #Int - stores the number of times this pokemon has been hit this battle, and does NOT reset when switching out.
        self.num_hits = 0

        # Abilities
        #Boolean - stores whether this poke's fire moves are boosted by flash fire.
        self.flash_fire = False
        #Int - stores the turn number relative to getting truant, % 2 == 1 -> loaf around.
        self.truant_turn = 0
        #Boolean - stores whether the ice face of this pokemon has been repaired.
        self.ice_repaired = False
        #Optional[Item] - stores the last berry ate by this pokemon.
        self.last_berry = None
        #ExpiringEffect - stores the number of turns until this pokemon attempts to recover & eat their last eaten berry.
        self.cud_chew = ExpiringEffect(0)
        #Boolean - stores whether booster_energy has been consumed this send out to activate the effects of Protosynthesis / Quark Drive.
        self.booster_energy = False
        #Boolean - stores whether supersweet_syrup has been consumed to lower the evasion of its opponent. NOT reset on switch out.
        self.supersweet_syrup = False

    def pretty_name(self):
        return self.name.replace("-", " ").title()

    def has_move(self, movename):
        for move in self.moves:
            if movename.lower() in move.name.lower():
                return True
        return False