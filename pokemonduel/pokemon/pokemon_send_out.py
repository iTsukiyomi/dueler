import random
from ..misc import ExpiringEffect, ExpiringItem, Metronome
from ..enums import Ability, ElementType, DamageClass


class DuelPokemonSendOut:
    """Pokemon send out and remove logic."""

    def send_out(self, otherpoke, battle):
            """
            Initalize a poke upon first sending it out.
            
            otherpoke may be None, if two pokes are sent out at the same time and the first is killed in the send out process.
            Returns a formatted message.
            """
            self.ever_sent_out = True
            
            # Emergency exit `remove`s the pokemon *in the middle of the turn* in a somewhat unsafe way.
            # `remove` may need to be called here, but that seems like it may have side effects.
            self.flinched = False
            
            # This has to go BEFORE the send out message, and not in send_out_ability as it only
            # applies on send out, not when abilities are changed, and it changes the send out msg.
            illusion_options = [x for x in self.owner.party if x is not self and x.hp > 0]
            if self.ability() == Ability.ILLUSION and illusion_options:
                self.illusion__name = self._name
                self.illusion_name = self.name
                self._name = illusion_options[-1]._name
                self.name = illusion_options[-1].name
            
            if self._name == "Pikachu":
                msg = f"{self.name}, I choose you!\n"
            else:
                msg = f"{self.owner.name} sent out {self.name}!\n"
            
            # Any time a poke switches out, certain effects it had put on its opponent end
            if otherpoke is not None:
                otherpoke.trapping = False
                otherpoke.octolock = False
                otherpoke.bind.set_turns(0)
            
            #Baton Pass
            if self.owner.baton_pass is not None:
                msg += f"{self.name} carries on the baton!\n"
                self.owner.baton_pass.apply(self)
                self.owner.baton_pass = None
            
            #Shed Tail
            if self.owner.next_substitute:
                self.substitute = self.owner.next_substitute
                self.owner.next_substitute = 0
            
            #Entry hazards
            #Special case for clearing toxic spikes, still happens even with heavy duty boots
            if self.owner.toxic_spikes and self.grounded(battle) and ElementType.POISON in self.type_ids:
                self.owner.toxic_spikes = 0
                msg += f"{self.name} absorbed the toxic spikes!\n"
            if self.held_item != "heavy-duty-boots":
                #Grounded entry hazards
                if self.grounded(battle):
                    #Spikes
                    if self.owner.spikes:
                        #1/8 -> 1/4
                        damage = self.starting_hp // (10 - (2 * self.owner.spikes))
                        msg += self.damage(damage, battle, source="spikes")
                    #Toxic spikes
                    if self.owner.toxic_spikes == 1:
                        msg += self.nv.apply_status("poison", battle, source="toxic spikes")
                    elif self.owner.toxic_spikes == 2:
                        msg += self.nv.apply_status("b-poison", battle, source="toxic spikes")
                    #Sticky web
                    if self.owner.sticky_web:
                        msg += self.append_speed(-1, source="the sticky web")
                #Non-grounded entry hazards
                if self.owner.stealth_rock:
                    effective = self.effectiveness(ElementType.ROCK, battle)
                    if effective:
                        # damage = 1/8 max hp * effectiveness
                        damage = self.starting_hp // (32 // (4 * effective))
                        msg += self.damage(int(damage), battle, source="stealth rock")
            
            if self.hp > 0:
                msg += self.send_out_ability(otherpoke, battle)
            
            #Restoration
            if self.owner.healing_wish:
                used = False
                if self.hp != self.starting_hp:
                    used = True
                    self.hp = self.starting_hp
                if self.nv.current:
                    used = True
                    self.nv.reset()
                if used:
                    self.owner.healing_wish = False
                    msg += f"{self.name} was restored by healing wish!\n"
            if self.owner.lunar_dance:
                used = False
                if self.hp != self.starting_hp:
                    used = True
                    self.hp = self.starting_hp
                if self.nv.current:
                    used = True
                    self.nv.reset()
                not_at_full_pp = [move for move in self.moves if move.pp != move.starting_pp]
                if not_at_full_pp:
                    used = True
                    for move in not_at_full_pp:
                        move.pp = move.starting_pp
                if used:
                    self.owner.lunar_dance = False
                    msg += f"{self.name} was restored by lunar dance\n"
            
            # Items
            if self.held_item == "air-balloon" and not self.grounded(battle):
                msg += f"{self.name} floats in the air with its air balloon!\n"
            if self.held_item == "electric-seed" and battle.terrain.item == "electric":
                msg += self.append_defense(1, attacker=self, source="its electric seed")
                self.held_item.use()
            if self.held_item == "psychic-seed" and battle.terrain.item == "psychic":
                msg += self.append_spdef(1, attacker=self, source="its psychic seed")
                self.held_item.use()
            if self.held_item == "misty-seed" and battle.terrain.item == "misty":
                msg += self.append_spdef(1, attacker=self, source="its misty seed")
                self.held_item.use()
            if self.held_item == "grassy-seed" and battle.terrain.item == "grassy":
                msg += self.append_defense(1, attacker=self, source="its grassy seed")
                self.held_item.use()
            msg += self.held_item.activate_on_switch_in(battle)
            return msg
        
    def send_out_ability(self, otherpoke, battle):
        """
        Initalize this poke's ability.
        
        otherpoke may be None.
        Returns a formatted message.
        """
        msg = ""
        
        #Imposter (sus)
        if self.ability() == Ability.IMPOSTER and otherpoke is not None and not otherpoke.substitute and otherpoke.illusion_name is None:
            msg += f"{self.name} transformed into {otherpoke._name}!\n"
            self.transform(otherpoke)
        
        #Weather
        if self.ability() == Ability.DRIZZLE:
            msg += battle.weather.set("rain", self)
        if self.ability() == Ability.PRIMORDIAL_SEA:
            msg += battle.weather.set("h-rain", self)
        if self.ability() == Ability.SAND_STREAM:
            msg += battle.weather.set("sandstorm", self)
        if self.ability() == Ability.SNOW_WARNING:
            msg += battle.weather.set("hail", self)
        if self.ability() in (Ability.DROUGHT, Ability.ORICHALCUM_PULSE):
            msg += battle.weather.set("sun", self)
        if self.ability() == Ability.DESOLATE_LAND:
            msg += battle.weather.set("h-sun", self)
        if self.ability() == Ability.DELTA_STREAM:
            msg += battle.weather.set("h-wind", self)
        
        #Terrain
        if self.ability() == Ability.GRASSY_SURGE:
            msg += battle.terrain.set("grassy", self)
        if self.ability() == Ability.MISTY_SURGE:
            msg += battle.terrain.set("misty", self)
        if self.ability() in (Ability.ELECTRIC_SURGE, Ability.HADRON_ENGINE):
            msg += battle.terrain.set("electric", self)
        if self.ability() == Ability.PSYCHIC_SURGE:
            msg += battle.terrain.set("psychic", self)
        
        # Message only
        if self.ability() == Ability.MOLD_BREAKER:
            msg += f"{self.name} breaks the mold!\n"
        if self.ability() == Ability.TURBOBLAZE:
            msg += f"{self.name} is radiating a blazing aura!\n"
        if self.ability() == Ability.TERAVOLT:
            msg += f"{self.name} is radiating a bursting aura!\n"
        
        if self.ability() == Ability.INTIMIDATE and otherpoke is not None:
            if otherpoke.ability() == Ability.OBLIVIOUS:
                msg += f"{otherpoke.name} is too oblivious to be intimidated!\n"
            elif otherpoke.ability() == Ability.OWN_TEMPO:
                msg += f"{otherpoke.name} keeps walking on its own tempo, and is not intimidated!\n"
            elif otherpoke.ability() == Ability.INNER_FOCUS:
                msg += f"{otherpoke.name} is too focused to be intimidated!\n"
            elif otherpoke.ability() == Ability.SCRAPPY:
                msg += f"{otherpoke.name} is too scrappy to be intimidated!\n"
            elif otherpoke.ability() == Ability.GUARD_DOG:
                msg += f"{otherpoke.name}'s guard dog keeps it from being intimidated!\n"
                msg += otherpoke.append_attack(1, attacker=otherpoke, source="its guard dog")
            else:
                msg += otherpoke.append_attack(-1, attacker=self, source=f"{self.name}'s Intimidate")
                if otherpoke.held_item == "adrenaline-orb":
                    msg += otherpoke.append_speed(1, attacker=otherpoke, source="its adrenaline orb")
                if otherpoke.ability() == Ability.RATTLED:
                    msg += otherpoke.append_speed(1, attacker=otherpoke, source="its rattled")
        if self.ability() == Ability.SCREEN_CLEANER:
            battle.trainer1.aurora_veil.set_turns(0)
            battle.trainer1.light_screen.set_turns(0)
            battle.trainer1.reflect.set_turns(0)
            battle.trainer2.aurora_veil.set_turns(0)
            battle.trainer2.light_screen.set_turns(0)
            battle.trainer2.reflect.set_turns(0)
            msg += f"{self.name}'s screen cleaner removed barriers from both sides of the field!\n"
        if self.ability() == Ability.INTREPID_SWORD:
            msg += self.append_attack(1, attacker=self, source="its intrepid sword")
        if self.ability() == Ability.DAUNTLESS_SHIELD:
            msg += self.append_defense(1, attacker=self, source="its dauntless shield")
        if self.ability() == Ability.TRACE and otherpoke is not None and otherpoke.ability_giveable():
            self.ability_id = otherpoke.ability_id
            msg += f"{self.name} traced {otherpoke.name}'s ability!\n"
            msg += self.send_out_ability(otherpoke, battle)
            return msg
        if self.ability() == Ability.DOWNLOAD and otherpoke is not None:
            if otherpoke.get_spdef(battle) > otherpoke.get_defense(battle):
                msg += self.append_attack(1, attacker=self, source="its download")
            else:
                msg += self.append_spatk(1, attacker=self, source="its download")
        if self.ability() == Ability.ANTICIPATION and otherpoke is not None:
            for move in otherpoke.moves:
                if move.effect == 39:
                    msg += f"{self.name} shuddered in anticipation!\n"
                    break
                if self.effectiveness(move.type, battle) > 1:
                    msg += f"{self.name} shuddered in anticipation!\n"
                    break
        if self.ability() == Ability.FOREWARN and otherpoke is not None:
            bestmoves = []
            bestpower = 0
            for move in otherpoke.moves:
                if move.damage_class == DamageClass.STATUS:
                    power = 0
                if move.effect == 39:
                    power = 150
                elif move.power is None: # Good enough
                    power = 80
                else:
                    power = move.power
                if power > bestpower:
                    bestpower = power
                    bestmoves = [move]
                elif power == bestpower:
                    bestmoves.append(move)
            if bestmoves:
                move = random.choice(bestmoves)
                msg += f"{self.name} is forewarned about {otherpoke.name}'s {move.pretty_name}!\n"
        if self.ability() == Ability.FRISK and otherpoke is not None and otherpoke.held_item.has_item():
            msg += f"{self.name} senses that {otherpoke.name} is holding a {otherpoke.held_item.name} using its frisk!\n"
        if self.ability() == Ability.MULTITYPE:
            e = None
            if self.held_item == "draco-plate":
                e = ElementType.DRAGON
                f = "Arceus-dragon"
            elif self.held_item == "dread-plate":
                e = ElementType.DARK
                f = "Arceus-dark"
            elif self.held_item == "earth-plate":
                e = ElementType.GROUND
                f = "Arceus-ground"
            elif self.held_item == "fist-plate":
                e = ElementType.FIGHTING
                f = "Arceus-fighting"
            elif self.held_item == "flame-plate":
                e = ElementType.FIRE
                f = "Arceus-fire"
            elif self.held_item == "icicle-plate":
                e = ElementType.ICE
                f = "Arceus-ice"
            elif self.held_item == "insect-plate":
                e = ElementType.BUG
                f = "Arceus-bug"
            elif self.held_item == "iron-plate":
                e = ElementType.STEEL
                f = "Arceus-steel"
            elif self.held_item == "meadow-plate":
                e = ElementType.GRASS
                f = "Arceus-grass"
            elif self.held_item == "mind-plate":
                e = ElementType.PSYCHIC
                f = "Arceus-psychic"
            elif self.held_item == "pixie-plate":
                e = ElementType.FAIRY
                f = "Arceus-fairy"
            elif self.held_item == "sky-plate":
                e = ElementType.FLYING
                f = "Arceus-flying"
            elif self.held_item == "splash-plate":
                e = ElementType.WATER
                f = "Arceus-water"
            elif self.held_item == "spooky-plate":
                e = ElementType.GHOST
                f = "Arceus-ghost"
            elif self.held_item == "stone-plate":
                e = ElementType.ROCK
                f = "Arceus-rock"
            elif self.held_item == "toxic-plate":
                e = ElementType.POISON
                f = "Arceus-poison"
            elif self.held_item == "zap-plate":
                e = ElementType.ELECTRIC
                f = "Arceus-electric"
            if e is not None and self.form(f):
                self.type_ids = [e]
                t = ElementType(e).name.lower()
                msg += f"{self.name} transformed into a {t} type using its multitype!\n"
        if self.ability() == Ability.RKS_SYSTEM and self._name == "Silvally":
            e = None
            if self.held_item == "dragon-memory":
                if self.form("Silvally-dragon"):
                    e = ElementType.DRAGON
            elif self.held_item == "dark-memory":
                if self.form("Silvally-dark"):
                    e = ElementType.DARK
            elif self.held_item == "ground-memory":
                if self.form("Silvally-ground"):
                    e = ElementType.GROUND
            elif self.held_item == "fighting-memory":
                if self.form("Silvally-fighting"):
                    e = ElementType.FIGHTING
            elif self.held_item == "fire-memory":
                if self.form("Silvally-fire"):
                    e = ElementType.FIRE
            elif self.held_item == "ice-memory":
                if self.form("Silvally-ice"):
                    e = ElementType.ICE
            elif self.held_item == "bug-memory":
                if self.form("Silvally-bug"):
                    e = ElementType.BUG
            elif self.held_item == "steel-memory":
                if self.form("Silvally-steel"):
                    e = ElementType.STEEL
            elif self.held_item == "grass-memory":
                if self.form("Silvally-grass"):
                    e = ElementType.GRASS
            elif self.held_item == "psychic-memory":
                if self.form("Silvally-psychic"):
                    e = ElementType.PSYCHIC
            elif self.held_item == "fairy-memory":
                if self.form("Silvally-fairy"):
                    e = ElementType.FAIRY
            elif self.held_item == "flying-memory":
                if self.form("Silvally-flying"):
                    e = ElementType.FLYING
            elif self.held_item == "water-memory":
                if self.form("Silvally-water"):
                    e = ElementType.WATER
            elif self.held_item == "ghost-memory":
                if self.form("Silvally-ghost"):
                    e = ElementType.GHOST
            elif self.held_item == "rock-memory":
                if self.form("Silvally-rock"):
                    e = ElementType.ROCK
            elif self.held_item == "poison-memory":
                if self.form("Silvally-poison"):
                    e = ElementType.POISON
            elif self.held_item == "electric-memory":
                if self.form("Silvally-electric"):
                    e = ElementType.ELECTRIC
            if e is not None:
                self.type_ids = [e]
                t = ElementType(e).name.lower()
                msg += f"{self.name} transformed into a {t} type using its rks system!\n"
        if self.ability() == Ability.TRUANT:
            self.truant_turn = 0
        if self.ability() == Ability.FORECAST and self._name in ("Castform", "Castform-snowy", "Castform-rainy", "Castform-sunny"):
            weather = battle.weather.get()
            element = None
            if weather == "hail" and self._name != "Castform-snowy":
                if self.form("Castform-snowy"):
                    element = ElementType.ICE
            elif weather in ("sandstorm", "h-wind", None) and self._name != "Castform":
                if self.form("Castform"):
                    element = ElementType.NORMAL
            elif weather in ("rain", "h-rain") and self._name != "Castform-rainy":
                if self.form("Castform-rainy"):
                    element = ElementType.WATER
            elif weather in ("sun", "h-sun") and self._name != "Castform-sunny":
                if self.form("Castform-sunny"):
                    element = ElementType.FIRE
            if element is not None:
                self.type_ids = [element]
                t = ElementType(element).name.lower()
                msg += f"{self.name} transformed into a {t} type using its forecast!\n"
        if self.ability() == Ability.MIMICRY and battle.terrain.item:
            terrain = battle.terrain.item
            if terrain == "electric":
                element = ElementType.ELECTRIC
            elif terrain == "grassy":
                element = ElementType.GRASS
            elif terrain == "misty":
                element = ElementType.FAIRY
            elif terrain == "psychic":
                element = ElementType.PSYCHIC
            self.type_ids = [element]
            t = ElementType(element).name.lower()
            msg += f"{self.name} transformed into a {t} type using its mimicry!\n"
        if self.ability() == Ability.WIND_RIDER and self.owner.tailwind.active():
            msg += self.append_attack(1, attacker=self, source="its wind rider")
        if self.ability() == Ability.SUPERSWEET_SYRUP and not self.supersweet_syrup and otherpoke is not None:
            msg += otherpoke.append_evasion(-1, attacker=self, source=f"{self.name}'s supersweet syrup")
        
        return msg
    
    def remove(self, battle, *, fainted=False):
        """
        Clean up a poke when it is removed from battle.
        
        Returns a formatted message of anything that happened while switching out.
        """
        msg = ""
        if not fainted:
            if self.ability() == Ability.NATURAL_CURE and self.nv.current:
                msg += f"{self.name}'s {self.nv.current} was cured by its natural cure!\n"
                self.nv.reset()
            if self.ability() == Ability.REGENERATOR:
                msg += self.heal(self.starting_hp // 3, source="its regenerator")
            if self.ability() == Ability.ZERO_TO_HERO:
                if self.form("Palafin-hero"):
                    msg += f"{self.name} is ready to be a hero!\n"
        self.nv.badly_poisoned_turn = 0
        self.minimized = False
        self.has_moved = False
        self.choice_move = None
        self.last_move = None
        self.should_mega_evolve = False
        self.swapped_in = False
        self.active_turns = 0
        if self.illusion__name is not None:
            self._name = self.illusion__name
            self.name = self.illusion_name
        self.illusion__name = None
        self.illusion_name = None
        if self._starting_name in ("Ditto", "Smeargle", "Mew", "Aegislash"):
            self._name = self._starting_name
            if self._nickname != "None":
                self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
            else:
                self.name = self._name.replace("-", " ")
        if self.owner.current_pokemon is self:
            self.owner.current_pokemon = None
        if battle.weather.recheck_ability_weather():
            msg += "The weather cleared!\n"
        # Look up base stats for the current form name. If the form is
        # missing from the table (e.g. a rare regional/mega variant whose
        # key differs from the engine's ``_name``), fall back to the
        # starting name. If that's also missing, keep the live stats and
        # log a warning instead of crashing the whole battle — this is
        # what was causing the ``KeyError: 'moltres'`` / ``'dewgong'``
        # crashes in self-play.
        _stats_key = None
        if self._name in self.base_stats:
            _stats_key = self._name
        elif getattr(self, "_starting_name", None) in self.base_stats:
            _stats_key = self._starting_name
        if _stats_key is not None:
            _row = self.base_stats[_stats_key]
            self.attack  = _row[1]
            self.defense = _row[2]
            self.spatk   = _row[3]
            self.spdef   = _row[4]
            self.speed   = _row[5]
        else:
            try:
                import logging as _logging
                _logging.getLogger("dueler.pokemon").warning(
                    "base_stats missing key %r (starting=%r); keeping current stats",
                    self._name, getattr(self, "_starting_name", None),
                )
            except Exception:
                pass
        self.hpiv = self.starting_hpiv
        self.atkiv = self.starting_atkiv
        self.defiv = self.starting_defiv
        self.spatkiv = self.starting_spatkiv
        self.spdefiv = self.starting_spdefiv
        self.speedev = self.starting_speedev
        self.hpev = self.starting_hpev
        self.atkev = self.starting_atkev
        self.defev = self.starting_defev
        self.spatkev = self.starting_spatkev
        self.spdefev = self.starting_spdefev
        self.speedev = self.starting_speedev
        self.moves = self.starting_moves.copy()
        self.ability_id = self.starting_ability_id
        self.type_ids = self.starting_type_ids.copy()
        self.attack_stage = 0
        self.defense_stage = 0
        self.spatk_stage = 0
        self.spdef_stage = 0
        self.speed_stage = 0
        self.accuracy_stage = 0
        self.evasion_stage = 0
        self.metronome = Metronome()
        self.leech_seed = False
        self.stockpile = 0
        self.flinched = False
        self.confusion = ExpiringEffect(0)
        self.last_move_damage = None
        self.locked_move = None
        self.bide = None
        self.torment = False
        self.imprison = False
        self.disable = ExpiringItem()
        self.taunt = ExpiringEffect(0)
        self.encore = ExpiringItem()
        self.heal_block = ExpiringEffect(0)
        self.focus_energy = False
        self.perish_song = ExpiringEffect(0)
        self.nightmare = False
        self.defense_curl = False
        self.fury_cutter = 0
        self.bind = ExpiringEffect(0)
        self.substitute = 0
        self.silenced = ExpiringEffect(0)
        self.last_move_failed = False
        self.rage = False
        self.mind_reader = ExpiringItem()
        self.destiny_bond = False
        self.destiny_bond_cooldown = ExpiringEffect(0)
        self.trapping = False
        self.ingrain = False
        self.infatuated = None
        self.aqua_ring = False
        self.magnet_rise = ExpiringEffect(0)
        self.dive = False
        self.dig = False
        self.fly = False
        self.shadow_force = False
        self.lucky_chant = ExpiringEffect(0)
        self.grounded_by_move = False
        self.charge = ExpiringEffect(0)
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
        self.autotomize = 0
        self.lansat_berry_ate = False
        self.micle_berry_ate = False
        self.flash_fire = False
        self.truant_turn = 0
        self.cud_chew = ExpiringEffect(0)
        self.booster_energy = False
        self.stat_increased = False
        self.stat_decreased = False
        self.roost = False
        self.octolock = False
        self.attack_split = None
        self.spatk_split = None
        self.defense_split = None
        self.spdef_split = None
        self.tar_shot = False
        self.syrup_bomb = ExpiringEffect(0)
        self.held_item.ever_had_item = self.held_item.item is not None

        return msg