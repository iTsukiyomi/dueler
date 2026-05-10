from ..enums import Ability, ElementType


class DuelPokemonStats:
    """Pokemon stat calculation and modification logic."""

    def calculate_raw_stat(self, base, iv, ev, nature):
        """
        Helper function to calculate a raw stat using the base, IV, EV, level, and nature.
        
        https://bulbapedia.bulbagarden.net/wiki/Stat#Determination_of_stats "In Generation III onward"
        """
        return round((((2 * base + iv + (ev / 4)) * self.level) / 100) + 5) * nature
    
    @staticmethod
    def calculate_stat(stat, stat_stage, *, crop=False):
        """Calculates a stat based on that stat's stage changes."""
        if crop == "bottom":
            stat_stage = max(stat_stage, 0)
        elif crop == "top":
            stat_stage = min(stat_stage, 0)
        stage_multiplier = {
            -6: 2/8,
            -5: 2/7,
            -4: 2/6,
            -3: 2/5,
            -2: 2/4,
            -1: 2/3,
            0: 1,
            1: 3/2,
            2: 2,
            3: 5/2,
            4: 3,
            5: 7/2,
            6: 4,
        }
        return stage_multiplier[stat_stage] * stat
    
    def get_raw_attack(self, *, check_power_trick=True, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_trick and check_power_trick:
            return self.get_raw_defense(check_power_trick=False, check_power_shift=check_power_shift)
        if self.power_shift and check_power_shift:
            return self.get_raw_defense(check_power_trick=check_power_trick, check_power_shift=False)
        stat = self.calculate_raw_stat(self.attack, self.atkiv, self.atkev, self.nature_stat_deltas["Attack"])
        if self.attack_split is not None:
            stat = (stat + self.attack_split) // 2
        return stat
    
    def get_raw_defense(self, *, check_power_trick=True, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_trick and check_power_trick:
            return self.get_raw_attack(check_power_trick=False, check_power_shift=check_power_shift)
        if self.power_shift and check_power_shift:
            return self.get_raw_attack(check_power_trick=check_power_trick, check_power_shift=False)
        stat = self.calculate_raw_stat(self.defense, self.defiv, self.defev, self.nature_stat_deltas["Defense"])
        if self.defense_split is not None:
            stat = (stat + self.defense_split) // 2
        return stat
    
    def get_raw_spatk(self, *, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_shift and check_power_shift:
            return self.get_raw_spdef(check_power_shift=False)
        stat = self.calculate_raw_stat(self.spatk, self.spatkiv, self.spatkev, self.nature_stat_deltas["Special attack"])
        if self.spatk_split is not None:
            stat = (stat + self.spatk_split) // 2
        return stat
    
    def get_raw_spdef(self, *, check_power_shift=True):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        if self.power_shift and check_power_shift:
            return self.get_raw_spatk(check_power_shift=False)
        stat = self.calculate_raw_stat(self.spdef, self.spdefiv, self.spdefev, self.nature_stat_deltas["Special defense"])
        if self.spdef_split is not None:
            stat = (stat + self.spdef_split) // 2
        return stat
    
    def get_raw_speed(self):
        """Returns the raw attack of this poke, taking into account IVs EVs and natures and forms."""
        return self.calculate_raw_stat(self.speed, self.speediv, self.speedev, self.nature_stat_deltas["Speed"])
    
    def get_paradox_boosted_stat(self):
        stats = [
            ("attack", self.get_raw_attack()),
            ("defense", self.get_raw_defense()),
            ("spatk", self.get_raw_spatk()),
            ("spdef", self.get_raw_spdef()),
            ("speed", self.get_raw_speed())
        ]
        return max(stats, key=lambda x: x[1])[0]

    def is_paradox_active(self, battle):
        if self.ability() == Ability.PROTOSYNTHESIS:
            if battle.weather.get() in ("sun", "h-sun"):
                return True
            if self.booster_energy:
                return True
            if self.held_item == "booster-energy":
                self.held_item.use()
                self.booster_energy = True
                return True
        elif self.ability() == Ability.QUARK_DRIVE:
            if battle.terrain.item == "electric":
                return True
            if self.booster_energy:
                return True
            if self.held_item == "booster-energy":
                self.held_item.use()
                self.booster_energy = True
                return True
        return False

    def get_attack(self, battle, *, critical=False, ignore_stages=False):
        """Helper method to call calculate_stat for attack."""
        attack = self.get_raw_attack()
        if not ignore_stages:
            attack = self.calculate_stat(attack, self.attack_stage, crop="bottom" if critical else False)
        if self.ability() == Ability.GUTS and self.nv.current:
            attack *= 1.5
        if self.ability() == Ability.SLOW_START and self.active_turns < 5:
            attack *= .5
        if self.ability() in (Ability.HUGE_POWER, Ability.PURE_POWER):
            attack *= 2
        if self.ability() == Ability.HUSTLE:
            attack *= 1.5
        if self.ability() == Ability.DEFEATIST and self.hp <= self.starting_hp / 2:
            attack *= .5
        if self.ability() == Ability.GORILLA_TACTICS:
            attack *= 1.5
        if self.ability() == Ability.FLOWER_GIFT and battle.weather.get() in ("sun", "h-sun"):
            attack *= 1.5
        if self.ability() == Ability.ORICHALCUM_PULSE and battle.weather.get() in ("sun", "h-sun"):
            attack *= 4/3
        if self.held_item == "choice-band":
            attack *= 1.5
        if self.held_item == "light-ball" and self._name == "Pikachu":
            attack *= 2
        if self.held_item == "thick-club" and self._name in ("Cubone", "Marowak", "Marowak-alola"):
            attack *= 2
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.TABLETS_OF_RUIN:
                attack *= .75
        if self.is_paradox_active(battle) and self.get_paradox_boosted_stat() == "attack":
            attack *= 1.3
        attack *= self.held_item.get_stat_multiplier("attack")
        return attack
    
    def get_defense(self, battle, *, critical=False, ignore_stages=False, attacker=None, move=None):
        """Helper method to call calculate_stat for defense."""
        if battle.wonder_room.active():
            defense = self.get_raw_spdef()
        else:
            defense = self.get_raw_defense()
        if not ignore_stages:
            defense = self.calculate_stat(defense, self.defense_stage, crop="top" if critical else False)
        if self.ability(attacker=attacker, move=move) == Ability.MARVEL_SCALE and self.nv.current:
            defense *= 1.5
        if self.ability(attacker=attacker, move=move) == Ability.FUR_COAT:
            defense *= 2
        if self.ability(attacker=attacker, move=move) == Ability.GRASS_PELT and battle.terrain.item == "grassy":
            defense *= 1.5
        if self.held_item == "eviolite" and self.can_still_evolve:
            defense *= 1.5
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.SWORD_OF_RUIN:
                defense *= .75
        if self.is_paradox_active(battle) and self.get_paradox_boosted_stat() == "defense":
            defense *= 1.3
        defense *= self.held_item.get_stat_multiplier("defense")
        return defense
    
    def get_spatk(self, battle, *, critical=False, ignore_stages=False):
        """Helper method to call calculate_stat for spatk."""
        spatk = self.get_raw_spatk()
        if not ignore_stages:
            spatk = self.calculate_stat(spatk, self.spatk_stage, crop="bottom" if critical else False)
        if self.ability() == Ability.DEFEATIST and self.hp <= self.starting_hp / 2:
            spatk *= .5
        if self.ability() == Ability.SOLAR_POWER and battle.weather.get() in ("sun", "h-sun"):
            spatk *= 1.5
        if self.ability() == Ability.HADRON_ENGINE and battle.terrain.item == "grassy":
            spatk *= 4/3
        if self.held_item == "choice-specs":
            spatk *= 1.5
        if self.held_item == "deep-sea-tooth" and self._name == "Clamperl":
            spatk *= 2
        if self.held_item == "light-ball" and self._name == "Pikachu":
            spatk *= 2
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.VESSEL_OF_RUIN:
                spatk *= .75
        if self.is_paradox_active(battle) and self.get_paradox_boosted_stat() == "spatk":
            spatk *= 1.3
        spatk *= self.held_item.get_stat_multiplier("spatk")
        return spatk
    
    def get_spdef(self, battle, *, critical=False, ignore_stages=False, attacker=None, move=None):
        """Helper method to call calculate_stat for spdef."""
        if battle.wonder_room.active():
            spdef = self.get_raw_defense()
        else:
            spdef = self.get_raw_spdef()
        if not ignore_stages:
            spdef = self.calculate_stat(spdef, self.spdef_stage, crop="top" if critical else False)
        if battle.weather.get() == "sandstorm" and ElementType.ROCK in self.type_ids:
            spdef *= 1.5
        if self.ability(attacker=attacker, move=move) == Ability.FLOWER_GIFT and battle.weather.get() in ("sun", "h-sun"):
            spdef *= 1.5
        if self.held_item == "deep-sea-scale" and self._name == "Clamperl":
            spdef *= 2
        if self.held_item == "assault-vest":
            spdef *= 1.5
        if self.held_item == "eviolite" and self.can_still_evolve:
            spdef *= 1.5
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.BEADS_OF_RUIN:
                spdef *= .75
        if self.is_paradox_active(battle) and self.get_paradox_boosted_stat() == "spdef":
            spdef *= 1.3
        spdef *= self.held_item.get_stat_multiplier("spdef")
        return spdef
    
    def get_speed(self, battle):
        """Helper method to call calculate_stat for speed."""
        #Always active stage changes
        speed = self.calculate_stat(self.get_raw_speed(), self.speed_stage)
        if self.nv.paralysis() and not self.ability() == Ability.QUICK_FEET:
            speed //= 2
        if self.held_item == "iron-ball":
            speed //= 2
        if self.owner.tailwind.active():
            speed *= 2
        if self.ability() == Ability.SLUSH_RUSH and battle.weather.get() == "hail":
            speed *= 2
        if self.ability() == Ability.SAND_RUSH and battle.weather.get() == "sandstorm":
            speed *= 2
        if self.ability() == Ability.SWIFT_SWIM and battle.weather.get() in ("rain", "h-rain"):
            speed *= 2
        if self.ability() == Ability.CHLOROPHYLL and battle.weather.get() in ("sun", "h-sun"):
            speed *= 2
        if self.ability() == Ability.SLOW_START and self.active_turns < 5:
            speed *= .5
        if self.ability() == Ability.UNBURDEN and not self.held_item.has_item() and self.held_item.ever_had_item:
            speed *= 2
        if self.ability() == Ability.QUICK_FEET and self.nv.current:
            speed *= 1.5
        if self.ability() == Ability.SURGE_SURFER and battle.terrain.item == "electric":
            speed *= 2
        if self.held_item == "choice-scarf":
            speed *= 1.5
        if self.is_paradox_active(battle) and self.get_paradox_boosted_stat() == "speed":
            speed *= 1.5
        speed *= self.held_item.get_stat_multiplier("speed")
        speed *= self.held_item.get_speed_multiplier()
        return speed
    
    def get_accuracy(self, battle):
        """Helper method to calculate accuracy stage."""
        return self.accuracy_stage
        
    def get_evasion(self, battle):
        """Helper method to calculate evasion stage."""
        return self.evasion_stage
    
    def append_attack(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for attack."""
        return self.append_stat(stage_change, attacker, move, "attack", source, check_looping)
    
    def append_defense(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for defense."""
        return self.append_stat(stage_change, attacker, move, "defense", source, check_looping)
    
    def append_spatk(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for special attack."""
        return self.append_stat(stage_change, attacker, move, "special attack", source, check_looping)
    
    def append_spdef(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for special defense."""
        return self.append_stat(stage_change, attacker, move, "special defense", source, check_looping)
    
    def append_speed(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for speed."""
        return self.append_stat(stage_change, attacker, move, "speed", source, check_looping)
    
    def append_accuracy(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for accuracy."""
        return self.append_stat(stage_change, attacker, move, "accuracy", source, check_looping)
    
    def append_evasion(self, stage_change: int, *, attacker=None, move=None, source: str="", check_looping: bool=True):
        """Helper method to call append_stat for evasion."""
        return self.append_stat(stage_change, attacker, move, "evasion", source, check_looping)
        
    def append_stat(self, stage_change: int, attacker, move, stat: str, source: str, check_looping: bool=True):
        """
        Adds a stat stage change to this pokemon.
        
        Returns a formatted string describing the stat change.
        """
        msg = ""
        if self.substitute and attacker is not self and attacker is not None and (move is None or move.is_affected_by_substitute()):
            return ""
        if source:
            source = f" from {source}"
        delta_msgs = {
            -3: f"{self.name}'s {stat} severely fell{source}!\n",
            -2: f"{self.name}'s {stat} harshly fell{source}!\n",
            -1: f"{self.name}'s {stat} fell{source}!\n",
            1: f"{self.name}'s {stat} rose{source}!\n",
            2: f"{self.name}'s {stat} rose sharply{source}!\n",
            3: f"{self.name}'s {stat} rose drastically{source}!\n",
        }
        delta = stage_change
        if self.ability(attacker=attacker, move=move) == Ability.SIMPLE:
            delta *= 2
        if self.ability(attacker=attacker, move=move) == Ability.CONTRARY:
            delta *= -1
        
        if stat == "attack":
            current_stage = self.attack_stage
        elif stat == "defense":
            current_stage = self.defense_stage
        elif stat == "special attack":
            current_stage = self.spatk_stage
        elif stat == "special defense":
            current_stage = self.spdef_stage
        elif stat == "speed":
            current_stage = self.speed_stage
        elif stat == "accuracy":
            current_stage = self.accuracy_stage
        elif stat == "evasion":
            current_stage = self.evasion_stage
        else:
            raise ValueError(f"invalid stat {stat}")
        
        # Cap stat stages within -6 to 6
        if delta < 0:
            #-6 -5 -4 ..  2
            # 0 -1 -2 .. -8
            cap = (current_stage * -1) - 6
            delta = max(delta, cap)
            if delta == 0:
                return f"{self.name}'s {stat} won't go any lower!\n"
        else:
            # 6  5  4 .. -2
            # 0  1  2 ..  8
            cap = (current_stage * -1) + 6
            delta = min(delta, cap)
            if delta == 0:
                return f"{self.name}'s {stat} won't go any higher!\n"
        
        # Prevent stat changes
        if delta < 0 and attacker is not self:
            if self.ability(attacker=attacker, move=move) in (Ability.CLEAR_BODY, Ability.WHITE_SMOKE, Ability.FULL_METAL_BODY):
                ability_name = Ability(self.ability_id).pretty_name
                return f"{self.name}'s {ability_name} prevented its {stat} from being lowered!\n"
            if self.ability(attacker=attacker, move=move) == Ability.HYPER_CUTTER and stat == "attack":
                return f"{self.name}'s claws stayed sharp because of its hyper cutter!\n"
            if self.ability(attacker=attacker, move=move) == Ability.KEEN_EYE and stat == "accuracy":
                return f"{self.name}'s aim stayed true because of its keen eye!\n"
            if self.ability(attacker=attacker, move=move) == Ability.MINDS_EYE and stat == "accuracy":
                return f"{self.name}'s aim stayed true because of its mind's eye!\n"
            if self.ability(attacker=attacker, move=move) == Ability.BIG_PECKS and stat == "defense":
                return f"{self.name}'s defense stayed strong because of its big pecks!\n"
            if self.owner.mist.active() and (attacker is None or attacker.ability() != Ability.INFILTRATOR):
                return f"The mist around {self.name}'s feet prevented its {stat} from being lowered!\n"
            if self.ability(attacker=attacker, move=move) == Ability.FLOWER_VEIL and ElementType.GRASS in self.type_ids:
                return ""
            if self.ability(attacker=attacker, move=move) == Ability.MIRROR_ARMOR and attacker is not None and check_looping:
                msg += f"{self.name} reflected the stat change with its mirror armor!\n"
                msg += attacker.append_stat(delta, self, None, stat, "", check_looping=False)
                return msg
        
        # Remember if stats were changed for certain moves
        if delta > 0:
            self.stat_increased = True
        elif delta < 0:
            self.stat_decreased = True
        
        if stat == "attack":
            self.attack_stage += delta
        elif stat == "defense":
            self.defense_stage += delta
        elif stat == "special attack":
            self.spatk_stage += delta
        elif stat == "special defense":
            self.spdef_stage += delta
        elif stat == "speed":
            self.speed_stage += delta
        elif stat == "accuracy":
            self.accuracy_stage += delta
        elif stat == "evasion":
            self.evasion_stage += delta
        else:
            raise ValueError(f"invalid stat {stat}")
        
        formatted_delta = min(max(delta, -3), 3)
        msg += delta_msgs[formatted_delta]

        # TODO: fix this hacky way of doing this, but probably not until multi battles...
        battle = self.held_item.battle

        # Effects that happen after a pokemon gains stats
        if delta < 0:
            if attacker is not self:
                if self.ability(attacker=attacker, move=move) == Ability.DEFIANT:
                    msg += self.append_attack(2, attacker=self, source="its defiance")
                if self.ability(attacker=attacker, move=move) == Ability.COMPETITIVE:
                    msg += self.append_spatk(2, attacker=self, source="its competitiveness")
            if self.held_item == "eject-pack":
                # This assumes that neither attacker or poke are needed if not checking traps
                swaps = self.owner.valid_swaps(..., ..., check_trap=False)
                if swaps:
                    msg += f"{self.name} is switched out by its eject pack!\n"
                    self.held_item.use()
                    msg += self.remove(battle)
                    # Force this pokemon to immediately return to be attacked
                    self.owner.mid_turn_remove = True
        elif delta > 0:
            for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
                if poke is not None and poke is not self and poke.ability() == Ability.OPPORTUNIST and check_looping:
                    msg += f"{poke.name} seizes the opportunity to boost its stat with its opportunist!\n"
                    msg += poke.append_stat(delta, poke, None, stat, "", check_looping=False)
        return msg
    
    def grounded(self, battle, *, attacker=None, move=None):
        """
        Returns True if this pokemon is considered "grounded".
        
        Explicit grounding applies first, then explicit ungrounding, then implicit grounding.
        """
        if battle.gravity.active():
            return True
        if self.held_item == "iron-ball":
            return True
        if self.grounded_by_move:
            return True
        if ElementType.FLYING in self.type_ids and not self.roost:
            return False
        if self.ability(attacker=attacker, move=move) == Ability.LEVITATE:
            return False
        if self.held_item == "air-balloon":
            return False
        if self.magnet_rise.active():
            return False
        if self.telekinesis.active():
            return False
        return True