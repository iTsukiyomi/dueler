import random
from ..enums import Ability, ElementType


class DuelPokemonTurn:
    """Pokemon turn-based logic."""

    def next_turn(self, otherpoke, battle):
        """
        Updates this pokemon for a new turn.
        
        `otherpoke` may be None if the opponent fainted the previous turn.
        Returns a formatted message.
        """
        msg = ""
        # This needs to be here, as swapping sets this value explicitly
        self.has_moved = False
        if not self.swapped_in:
            self.active_turns += 1
        self.last_move_damage = None
        self.last_move_failed = False
        self.should_mega_evolve = False
        self.rage = False
        self.mind_reader.next_turn()
        self.charge.next_turn()
        self.destiny_bond_cooldown.next_turn()
        self.magic_coat = False
        self.ion_deluge = False
        self.electrify = False
        if not self.protection_used:
            self.protection_chance = 1
        self.protection_used = False
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
        self.laser_focus.next_turn()
        self.powdered = False
        self.snatching = False
        if not self.echoed_voice_used:
            self.echoed_voice_power = 40
        self.grudge = False
        self.beak_blast = False
        self.dmg_this_turn = False
        if self.locked_move:
            if self.locked_move.next_turn():
                self.locked_move = None
                # Just in case they never actually used the move to remove it
                self.dive = False
                self.dig = False
                self.fly = False
                self.shadow_force = False
        self.fairy_lock.next_turn()
        self.flinched = False
        self.truant_turn += 1
        self.stat_increased = False
        self.stat_decreased = False
        self.roost = False
        self.syrup_bomb.next_turn()
        
        msg += self.nv.next_turn(battle)
        
        # Volatile status turn progression
        prev_disab_move = self.disable.item
        if self.disable.next_turn():
            msg += f"{self.name}'s {prev_disab_move.pretty_name} is no longer disabled!\n"
        if self.taunt.next_turn():
            msg += f"{self.name}'s taunt has ended!\n"
        if self.heal_block.next_turn():
            msg += f"{self.name}'s heal block has ended!\n"
        if self.silenced.next_turn():
            msg += f"{self.name}'s voice returned!\n"
        if self.magnet_rise.next_turn():
            msg += f"{self.name}'s magnet rise has ended!\n"
        if self.lucky_chant.next_turn():
            msg += f"{self.name} is no longer shielded by lucky chant!\n"
        if self.uproar.next_turn():
            msg += f"{self.name} calms down!\n"
        if self.telekinesis.next_turn():
            msg += f"{self.name} was released from telekinesis!\n"
        if self.embargo.next_turn():
            msg += f"{self.name}'s embargo was lifted!\n"
        if self.yawn.next_turn():
            msg += self.nv.apply_status("sleep", battle, attacker=self, source="drowsiness")
        if self.encore.next_turn():
            msg += f"{self.name}'s encore is over!\n"
        if self.perish_song.next_turn():
            msg += self.faint(battle, source="perish song")
        if self.encore.active() and self.encore.item.pp == 0:
            self.encore.end()
            msg += f"{self.name}'s encore is over!\n"
        if self.cud_chew.next_turn() and self.held_item.last_used is not None and self.held_item.last_used.name.endswith("-berry"):
            self.held_item.recover(self.held_item)
            msg += self.held_item.eat_berry()
            self.held_item.last_used = None

        
        # Abilities
        if self.ability() == Ability.SPEED_BOOST and not self.swapped_in:
            msg += self.append_speed(1, attacker=self, source="its Speed boost")
        if self.ability() == Ability.LIMBER and self.nv.paralysis():
            self.nv.reset()
            msg += f"{self.name}'s limber cured it of its paralysis!\n"
        if self.ability() == Ability.INSOMNIA and self.nv.sleep():
            self.nv.reset()
            msg += f"{self.name}'s insomnia woke it up!\n"
        if self.ability() == Ability.VITAL_SPIRIT and self.nv.sleep():
            self.nv.reset()
            msg += f"{self.name}'s vital spirit woke it up!\n"
        if self.ability() == Ability.IMMUNITY and self.nv.poison():
            self.nv.reset()
            msg += f"{self.name}'s immunity cured it of its poison!\n"
        if self.ability() == Ability.MAGMA_ARMOR and self.nv.freeze():
            self.nv.reset()
            msg += f"{self.name}'s magma armor cured it of thawed it!\n"
        if self.ability() in (Ability.WATER_VEIL, Ability.WATER_BUBBLE) and self.nv.burn():
            self.nv.reset()
            ability_name = Ability(self.ability_id).pretty_name
            msg += f"{self.name}'s {ability_name} cured it of its burn!\n"
        if self.ability() == Ability.OWN_TEMPO and self.confusion.active():
            self.confusion.set_turns(0)
            msg += f"{self.name}'s tempo cured it of its confusion!\n"
        if self.ability() == Ability.OBLIVIOUS:
            if self.infatuated:
                self.infatuated = None
                msg += f"{self.name} fell out of love because of its obliviousness!\n"
            if self.taunt.active():
                self.taunt.set_turns(0)
                msg += f"{self.name} stopped caring about being taunted because of its obliviousness!\n"
        if self.ability() == Ability.RAIN_DISH and battle.weather.get() in ("rain", "h-rain"):
            msg += self.heal(self.starting_hp // 16, source="its rain dish")
        if self.ability() == Ability.ICE_BODY and battle.weather.get() == "hail":
            msg += self.heal(self.starting_hp // 16, source="its ice body")
        if self.ability() == Ability.DRY_SKIN:
            if battle.weather.get() in ("rain", "h-rain"):
                msg += self.heal(self.starting_hp // 8, source="its dry skin")
            elif battle.weather.get() in ("sun", "h-sun"):
                msg += self.damage(self.starting_hp // 8, battle, source="its dry skin")
        if self.ability() == Ability.SOLAR_POWER and battle.weather.get() in ("sun", "h-sun"):
            msg += self.damage(self.starting_hp // 8, battle, source="its solar power")
        if self.ability() == Ability.MOODY:
            stats = [
                (self.attack_stage, "attack"),
                (self.defense_stage, "defense"),
                (self.spatk_stage, "special attack"),
                (self.spdef_stage, "special defense"),
                (self.speed_stage, "speed")
            ]
            add_stats = stats.copy()
            remove_stats = stats.copy()
            for stat in stats:
                if stat[0] == 6:
                    add_stats.remove(stat)
            add_stat = None
            if add_stats:
                add_stat = random.choice(add_stats)
                msg += self.append_stat(2, self, None, add_stat[1], "its moodiness")
            for stat in stats:
                if stat == add_stat:
                    remove_stats.remove(stat)
                if stat[0] == -6:
                    remove_stats.remove(stat)
            if remove_stats:
                remove_stat = random.choice(remove_stats)
                msg += self.append_stat(-1, self, None, remove_stat[1], "its moodiness")
        if (
            self.ability() == Ability.PICKUP
            and not self.held_item.has_item()
            and otherpoke is not None
            and otherpoke.held_item.last_used is not None
        ):
            self.held_item.recover(otherpoke.held_item)
            msg += f"{self.name} picked up a {self.held_item.name}!\n"
        if self.ability() == Ability.ICE_FACE and not self.ice_repaired and self._name == "Eiscue-noice" and battle.weather.get() == "hail":
            if self.form("Eiscue"):
                self.ice_repaired = True
                msg += f"{self.name}'s ice face was restored by the hail!\n"
        if self.ability() == Ability.HARVEST and self.last_berry is not None and not self.held_item.has_item():
            if random.randint(0, 1):
                self.held_item.item = self.last_berry
                self.last_berry = None
                msg += f"{self.name} harvested a {self.held_item.name}!\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan" and self.hp < self.starting_hp / 2:
            if self.form("Darmanitan-zen"):
                if ElementType.PSYCHIC not in self.type_ids:
                    self.type_ids.append(ElementType.PSYCHIC)
                msg += f"{self.name} enters a zen state.\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-galar" and self.hp < self.starting_hp / 2:
            if self.form("Darmanitan-zen-galar"):
                if ElementType.FIRE not in self.type_ids:
                    self.type_ids.append(ElementType.FIRE)
                msg += f"{self.name} enters a zen state.\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-zen" and self.hp >= self.starting_hp / 2:
            if self.form("Darmanitan"):
                if ElementType.PSYCHIC in self.type_ids:
                    self.type_ids.remove(ElementType.PSYCHIC)
                msg += f"{self.name}'s zen state ends!\n"
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-zen-galar" and self.hp >= self.starting_hp / 2:
            if self.form("Darmanitan-galar"):
                if ElementType.FIRE in self.type_ids:
                    self.type_ids.remove(ElementType.FIRE)
                msg += f"{self.name}'s zen state ends!\n"
        if self.ability() == Ability.SHIELDS_DOWN and self._name == "Minior" and self.hp < self.starting_hp / 2:
            if self.id % 7 == 0:
                new_form = "Minior-red"
            elif self.id % 7 == 1:
                new_form = "Minior-orange"
            elif self.id % 7 == 2:
                new_form = "Minior-yellow"
            elif self.id % 7 == 3:
                new_form = "Minior-green"
            elif self.id % 7 == 4:
                new_form = "Minior-blue"
            elif self.id % 7 == 5:
                new_form = "Minior-indigo"
            else:
                new_form = "Minior-violet"
            if self.form(new_form):
                msg += f"{self.name}'s core was exposed!\n"
        if (
            self.ability() == Ability.SHIELDS_DOWN
            and self._name in ("Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet")
            and self.hp >= self.starting_hp / 2
        ):
            if self.form("Minior"):
                msg += f"{self.name}'s shell returned!\n"
        if self.ability() == Ability.SCHOOLING and self._name == "Wishiwashi-school" and self.hp < self.starting_hp / 4:
            if self.form("Wishiwashi"):
                msg += f"{self.name}'s school is gone!\n"
        if self.ability() == Ability.SCHOOLING and self._name == "Wishiwashi" and self.hp >= self.starting_hp / 4 and self.level >= 20:
            if self.form("Wishiwashi-school"):
                msg += f"{self.name} schools together!\n"
        if self.ability() == Ability.POWER_CONSTRUCT and self._name in ("Zygarde", "Zygarde-10") and self.hp < self.starting_hp / 2 and self.hp > 0:
            if self.form("Zygarde-complete"):
                msg += f"{self.name} is at full power!\n"
                # Janky way to raise the current HP of this poke, as it's new form has a higher HP stat. Note, this is NOT healing.
                new_hp = round((((2 * self.base_stats["Zygarde-complete"][0] + self.hpiv + (self.hpev / 4)) * self.level) / 100) + self.level + 10)
                self.hp = new_hp - (self.starting_hp - self.hp)
                self.starting_hp = new_hp
        if self.ability() == Ability.HUNGER_SWITCH:
            if self._name == "Morpeko":
                self.form("Morpeko-hangry")
            elif self._name == "Morpeko-hangry":
                self.form("Morpeko")
        if self.ability() == Ability.FLOWER_GIFT and self._name == "Cherrim" and battle.weather.get() in ("sun", "h-sun"):
            self.form("Cherrim-sunshine")
        if self.ability() == Ability.FLOWER_GIFT and self._name == "Cherrim-sunshine" and battle.weather.get() not in ("sun", "h-sun"):
            self.form("Cherrim")
        
        #Bad Dreams
        if otherpoke is not None and otherpoke.ability() == Ability.BAD_DREAMS and self.nv.sleep():
            msg += self.damage(self.starting_hp // 8, battle, source=f"{otherpoke.name}'s bad dreams")
        #Leech seed
        if self.leech_seed and otherpoke is not None:
            damage = self.starting_hp // 8
            msg += self.damage(damage, battle, attacker=otherpoke, drain_heal_ratio=1, source="leech seed")
        #Curse
        if self.curse:
            msg += self.damage(self.starting_hp // 4, battle, source="its curse")
        #Syrup bomb
        if self.syrup_bomb.active() and otherpoke is not None:
            msg += self.append_speed(-1, attacker=otherpoke, source="its syrup coating")
        
        #Weather damages
        if self.ability() == Ability.OVERCOAT:
            pass
        elif self.held_item == "safety-goggles":
            pass
        elif battle.weather.get() == "sandstorm":
            if (
                ElementType.ROCK not in self.type_ids
                and ElementType.GROUND not in self.type_ids
                and ElementType.STEEL not in self.type_ids
                and self.ability() not in (Ability.SAND_RUSH, Ability.SAND_VEIL, Ability.SAND_FORCE)
            ):
                msg += self.damage(self.starting_hp // 16, battle, source="the sandstorm")
        elif battle.weather.get() == "hail":
            if (
                ElementType.ICE not in self.type_ids
                and self.ability() not in (Ability.SNOW_CLOAK, Ability.ICE_BODY)
            ):
                msg += self.damage(self.starting_hp // 16, battle, source="the hail")
        
        #Bind
        if self.bind.next_turn():
            msg += f"{self.name} is no longer bound!\n"
        elif self.bind.active() and otherpoke is not None:
            if otherpoke.held_item == "binding-band":
                msg += self.damage(self.starting_hp // 6, battle, source=f"{otherpoke.name}'s bind")
            else:
                msg += self.damage(self.starting_hp // 8, battle, source=f"{otherpoke.name}'s bind")
        #Ingrain
        if self.ingrain:
            heal = self.starting_hp // 16
            if self.held_item == "big_root":
                heal = int(heal * 1.3)
            msg += self.heal(heal, source="ingrain")
        #Aqua Ring
        if self.aqua_ring:
            heal = self.starting_hp // 16
            if self.held_item == "big_root":
                heal = int(heal * 1.3)
            msg += self.heal(heal, source="aqua ring")
        #Octolock
        if self.octolock and otherpoke is not None:
            msg += self.append_defense(-1, attacker=self, source=f"{otherpoke.name}'s octolock")
            msg += self.append_spdef(-1, attacker=self, source=f"{otherpoke.name}'s octolock")
        #Grassy Terrain
        if battle.terrain.item == "grassy" and self.grounded(battle) and not self.heal_block.active():
            msg += self.heal(self.starting_hp // 16, source="grassy terrain")
        
        #Goes at the end so everything in this func that checks it handles it correctly
        self.swapped_in = False
        msg += self.held_item.activate_end_of_turn(battle)
        return msg