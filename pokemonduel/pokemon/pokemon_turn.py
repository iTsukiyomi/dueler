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
        self.has_moved = False
        if not self.swapped_in:
            # pyrefly: ignore [missing-attribute]
            self.active_turns += 1
        self.last_move_damage = None
        self.last_move_failed = False
        self.should_mega_evolve = False
        self.rage = False
        # pyrefly: ignore [missing-attribute]
        self.mind_reader.next_turn()
        # pyrefly: ignore [missing-attribute]
        self.charge.next_turn()
        # pyrefly: ignore [missing-attribute]
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
        # pyrefly: ignore [missing-attribute]
        self.laser_focus.next_turn()
        self.powdered = False
        self.snatching = False
        # pyrefly: ignore [missing-attribute]
        if not self.echoed_voice_used:
            self.echoed_voice_power = 40
        self.grudge = False
        self.beak_blast = False
        self.dmg_this_turn = False
        if self.locked_move:
            if self.locked_move.next_turn():
                self.locked_move = None
                self.dive = False
                self.dig = False
                self.fly = False
                self.shadow_force = False
        # pyrefly: ignore [missing-attribute]
        self.fairy_lock.next_turn()
        self.flinched = False
        # pyrefly: ignore [missing-attribute]
        self.truant_turn += 1
        self.stat_increased = False
        self.stat_decreased = False
        self.roost = False
        # pyrefly: ignore [missing-attribute]
        self.syrup_bomb.next_turn()

        # pyrefly: ignore [missing-attribute]
        msg += self.nv.next_turn(battle)

        # Volatile status turn progression
        # pyrefly: ignore [missing-attribute]
        prev_disab_move = self.disable.item
        # pyrefly: ignore [missing-attribute]
        if self.disable.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s {prev_disab_move.pretty_name} is no longer disabled!\n"
        # pyrefly: ignore [missing-attribute]
        if self.taunt.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s taunt has ended!\n"
        # pyrefly: ignore [missing-attribute]
        if self.heal_block.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s heal block has ended!\n"
        # pyrefly: ignore [missing-attribute]
        if self.silenced.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s voice returned!\n"
        # pyrefly: ignore [missing-attribute]
        if self.magnet_rise.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s magnet rise has ended!\n"
        # pyrefly: ignore [missing-attribute]
        if self.lucky_chant.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name} is no longer shielded by lucky chant!\n"
        # pyrefly: ignore [missing-attribute]
        if self.uproar.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name} calms down!\n"
        # pyrefly: ignore [missing-attribute]
        if self.telekinesis.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name} was released from telekinesis!\n"
        # pyrefly: ignore [missing-attribute]
        if self.embargo.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s embargo was lifted!\n"
        # pyrefly: ignore [missing-attribute]
        if self.yawn.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += self.nv.apply_status("sleep", battle, attacker=self, source="drowsiness")
        # pyrefly: ignore [missing-attribute]
        if self.encore.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s encore is over!\n"
        # pyrefly: ignore [missing-attribute]
        if self.perish_song.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += self.faint(battle, source="perish song")
        # pyrefly: ignore [missing-attribute]
        if self.encore.active() and self.encore.item.pp == 0:
            # pyrefly: ignore [missing-attribute]
            self.encore.end()
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s encore is over!\n"
        # pyrefly: ignore [missing-attribute]
        if self.cud_chew.next_turn() and self.held_item.last_used is not None and self.held_item.last_used.name.endswith("-berry"):
            # pyrefly: ignore [missing-attribute]
            self.held_item.recover(self.held_item)
            # pyrefly: ignore [missing-attribute]
            msg += self.held_item.eat_berry()
            # pyrefly: ignore [missing-attribute]
            self.held_item.last_used = None


        # Abilities
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.SPEED_BOOST and not self.swapped_in:
            # pyrefly: ignore [missing-attribute]
            msg += self.append_speed(1, attacker=self, source="its Speed boost")
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.LIMBER and self.nv.paralysis():
            # pyrefly: ignore [missing-attribute]
            self.nv.reset()
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s limber cured it of its paralysis!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.INSOMNIA and self.nv.sleep():
            # pyrefly: ignore [missing-attribute]
            self.nv.reset()
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s insomnia woke it up!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.VITAL_SPIRIT and self.nv.sleep():
            # pyrefly: ignore [missing-attribute]
            self.nv.reset()
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s vital spirit woke it up!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.IMMUNITY and self.nv.poison():
            # pyrefly: ignore [missing-attribute]
            self.nv.reset()
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s immunity cured it of its poison!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.MAGMA_ARMOR and self.nv.freeze():
            # pyrefly: ignore [missing-attribute]
            self.nv.reset()
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s magma armor cured it of thawed it!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() in (Ability.WATER_VEIL, Ability.WATER_BUBBLE) and self.nv.burn():
            # pyrefly: ignore [missing-attribute]
            self.nv.reset()
            # pyrefly: ignore [missing-attribute]
            ability_name = Ability(self.ability_id).pretty_name
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s {ability_name} cured it of its burn!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.OWN_TEMPO and self.confusion.active():
            # pyrefly: ignore [missing-attribute]
            self.confusion.set_turns(0)
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name}'s tempo cured it of its confusion!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.OBLIVIOUS:
            if self.infatuated:
                self.infatuated = None
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name} fell out of love because of its obliviousness!\n"
            # pyrefly: ignore [missing-attribute]
            if self.taunt.active():
                # pyrefly: ignore [missing-attribute]
                self.taunt.set_turns(0)
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name} stopped caring about being taunted because of its obliviousness!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.RAIN_DISH and battle.weather.get() in ("rain", "h-rain"):
            # pyrefly: ignore [missing-attribute]
            msg += self.heal(self.starting_hp // 16, source="its rain dish")
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.ICE_BODY and battle.weather.get() == "hail":
            # pyrefly: ignore [missing-attribute]
            msg += self.heal(self.starting_hp // 16, source="its ice body")
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.DRY_SKIN:
            if battle.weather.get() in ("rain", "h-rain"):
                # pyrefly: ignore [missing-attribute]
                msg += self.heal(self.starting_hp // 8, source="its dry skin")
            elif battle.weather.get() in ("sun", "h-sun"):
                # pyrefly: ignore [missing-attribute]
                msg += self.damage(self.starting_hp // 8, battle, source="its dry skin")
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.SOLAR_POWER and battle.weather.get() in ("sun", "h-sun"):
            # pyrefly: ignore [missing-attribute]
            msg += self.damage(self.starting_hp // 8, battle, source="its solar power")
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.MOODY:
            stats = [
                # pyrefly: ignore [missing-attribute]
                (self.attack_stage, "attack"),
                # pyrefly: ignore [missing-attribute]
                (self.defense_stage, "defense"),
                # pyrefly: ignore [missing-attribute]
                (self.spatk_stage, "special attack"),
                # pyrefly: ignore [missing-attribute]
                (self.spdef_stage, "special defense"),
                # pyrefly: ignore [missing-attribute]
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
                # pyrefly: ignore [missing-attribute]
                msg += self.append_stat(2, self, None, add_stat[1], "its moodiness")
            for stat in stats:
                if stat == add_stat:
                    remove_stats.remove(stat)
                if stat[0] == -6:
                    remove_stats.remove(stat)
            if remove_stats:
                remove_stat = random.choice(remove_stats)
                # pyrefly: ignore [missing-attribute]
                msg += self.append_stat(-1, self, None, remove_stat[1], "its moodiness")
        if (
            # pyrefly: ignore [missing-attribute]
            self.ability() == Ability.PICKUP
            # pyrefly: ignore [missing-attribute]
            and not self.held_item.has_item()
            and otherpoke is not None
            and otherpoke.held_item.last_used is not None
        ):
            # pyrefly: ignore [missing-attribute]
            self.held_item.recover(otherpoke.held_item)
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name} picked up a {self.held_item.name}!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.ICE_FACE and not self.ice_repaired and self._name == "Eiscue-noice" and battle.weather.get() == "hail":
            # pyrefly: ignore [missing-attribute]
            if self.form("Eiscue"):
                self.ice_repaired = True
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name}'s ice face was restored by the hail!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.HARVEST and self.last_berry is not None and not self.held_item.has_item():
            if random.randint(0, 1):
                # pyrefly: ignore [missing-attribute]
                self.held_item.item = self.last_berry
                self.last_berry = None
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name} harvested a {self.held_item.name}!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan" and self.hp < self.starting_hp / 2:
            # pyrefly: ignore [missing-attribute]
            if self.form("Darmanitan-zen"):
                # pyrefly: ignore [missing-attribute]
                if ElementType.PSYCHIC not in self.type_ids:
                    # pyrefly: ignore [missing-attribute]
                    self.type_ids.append(ElementType.PSYCHIC)
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name} enters a zen state.\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-galar" and self.hp < self.starting_hp / 2:
            # pyrefly: ignore [missing-attribute]
            if self.form("Darmanitan-zen-galar"):
                # pyrefly: ignore [missing-attribute]
                if ElementType.FIRE not in self.type_ids:
                    # pyrefly: ignore [missing-attribute]
                    self.type_ids.append(ElementType.FIRE)
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name} enters a zen state.\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-zen" and self.hp >= self.starting_hp / 2:
            # pyrefly: ignore [missing-attribute]
            if self.form("Darmanitan"):
                # pyrefly: ignore [missing-attribute]
                if ElementType.PSYCHIC in self.type_ids:
                    # pyrefly: ignore [missing-attribute]
                    self.type_ids.remove(ElementType.PSYCHIC)
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name}'s zen state ends!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.ZEN_MODE and self._name == "Darmanitan-zen-galar" and self.hp >= self.starting_hp / 2:
            # pyrefly: ignore [missing-attribute]
            if self.form("Darmanitan-galar"):
                # pyrefly: ignore [missing-attribute]
                if ElementType.FIRE in self.type_ids:
                    # pyrefly: ignore [missing-attribute]
                    self.type_ids.remove(ElementType.FIRE)
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name}'s zen state ends!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.SHIELDS_DOWN and self._name == "Minior" and self.hp < self.starting_hp / 2:
            # pyrefly: ignore [missing-attribute]
            if self.id % 7 == 0:
                new_form = "Minior-red"
            # pyrefly: ignore [missing-attribute]
            elif self.id % 7 == 1:
                new_form = "Minior-orange"
            # pyrefly: ignore [missing-attribute]
            elif self.id % 7 == 2:
                new_form = "Minior-yellow"
            # pyrefly: ignore [missing-attribute]
            elif self.id % 7 == 3:
                new_form = "Minior-green"
            # pyrefly: ignore [missing-attribute]
            elif self.id % 7 == 4:
                new_form = "Minior-blue"
            # pyrefly: ignore [missing-attribute]
            elif self.id % 7 == 5:
                new_form = "Minior-indigo"
            else:
                new_form = "Minior-violet"
            # pyrefly: ignore [missing-attribute]
            if self.form(new_form):
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name}'s core was exposed!\n"
        if (
            # pyrefly: ignore [missing-attribute]
            self.ability() == Ability.SHIELDS_DOWN
            # pyrefly: ignore [missing-attribute]
            and self._name in ("Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet")
            and self.hp >= self.starting_hp / 2
        ):
            # pyrefly: ignore [missing-attribute]
            if self.form("Minior"):
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name}'s shell returned!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.SCHOOLING and self._name == "Wishiwashi-school" and self.hp < self.starting_hp / 4:
            # pyrefly: ignore [missing-attribute]
            if self.form("Wishiwashi"):
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name}'s school is gone!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.SCHOOLING and self._name == "Wishiwashi" and self.hp >= self.starting_hp / 4 and self.level >= 20:
            # pyrefly: ignore [missing-attribute]
            if self.form("Wishiwashi-school"):
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name} schools together!\n"
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.POWER_CONSTRUCT and self._name in ("Zygarde", "Zygarde-10") and self.hp < self.starting_hp / 2 and self.hp > 0:
            # pyrefly: ignore [missing-attribute]
            if self.form("Zygarde-complete"):
                # pyrefly: ignore [missing-attribute]
                msg += f"{self.name} is at full power!\n"
                # Janky way to raise the current HP of this poke, as it's new form has a higher HP stat. Note, this is NOT healing.
                # pyrefly: ignore [missing-attribute]
                new_hp = round((((2 * self.base_stats["Zygarde-complete"][0] + self.hpiv + (self.hpev / 4)) * self.level) / 100) + self.level + 10)
                self.hp = new_hp - (self.starting_hp - self.hp)
                self.starting_hp = new_hp
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.HUNGER_SWITCH:
            # pyrefly: ignore [missing-attribute]
            if self._name == "Morpeko":
                # pyrefly: ignore [missing-attribute]
                self.form("Morpeko-hangry")
            elif self._name == "Morpeko-hangry":
                # pyrefly: ignore [missing-attribute]
                self.form("Morpeko")
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.FLOWER_GIFT and self._name == "Cherrim" and battle.weather.get() in ("sun", "h-sun"):
            # pyrefly: ignore [missing-attribute]
            self.form("Cherrim-sunshine")
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.FLOWER_GIFT and self._name == "Cherrim-sunshine" and battle.weather.get() not in ("sun", "h-sun"):
            # pyrefly: ignore [missing-attribute]
            self.form("Cherrim")

        #Bad Dreams
        # pyrefly: ignore [missing-attribute]
        if otherpoke is not None and otherpoke.ability() == Ability.BAD_DREAMS and self.nv.sleep():
            # pyrefly: ignore [missing-attribute]
            msg += self.damage(self.starting_hp // 8, battle, source=f"{otherpoke.name}'s bad dreams")
        #Leech seed
        # pyrefly: ignore [missing-attribute]
        if self.leech_seed and otherpoke is not None:
            damage = self.starting_hp // 8
            # pyrefly: ignore [missing-attribute]
            msg += self.damage(damage, battle, attacker=otherpoke, drain_heal_ratio=1, source="leech seed")
        #Curse
        # pyrefly: ignore [missing-attribute]
        if self.curse:
            # pyrefly: ignore [missing-attribute]
            msg += self.damage(self.starting_hp // 4, battle, source="its curse")
        #Syrup bomb
        # pyrefly: ignore [missing-attribute]
        if self.syrup_bomb.active() and otherpoke is not None:
            # pyrefly: ignore [missing-attribute]
            msg += self.append_speed(-1, attacker=otherpoke, source="its syrup coating")

        #Weather damages
        # pyrefly: ignore [missing-attribute]
        if self.ability() == Ability.OVERCOAT:
            pass
        # pyrefly: ignore [missing-attribute]
        elif self.held_item == "safety-goggles":
            pass
        elif battle.weather.get() == "sandstorm":
            if (
                # pyrefly: ignore [missing-attribute]
                ElementType.ROCK not in self.type_ids
                # pyrefly: ignore [missing-attribute]
                and ElementType.GROUND not in self.type_ids
                # pyrefly: ignore [missing-attribute]
                and ElementType.STEEL not in self.type_ids
                # pyrefly: ignore [missing-attribute]
                and self.ability() not in (Ability.SAND_RUSH, Ability.SAND_VEIL, Ability.SAND_FORCE)
            ):
                # pyrefly: ignore [missing-attribute]
                msg += self.damage(self.starting_hp // 16, battle, source="the sandstorm")
        elif battle.weather.get() == "hail":
            if (
                # pyrefly: ignore [missing-attribute]
                ElementType.ICE not in self.type_ids
                # pyrefly: ignore [missing-attribute]
                and self.ability() not in (Ability.SNOW_CLOAK, Ability.ICE_BODY)
            ):
                # pyrefly: ignore [missing-attribute]
                msg += self.damage(self.starting_hp // 16, battle, source="the hail")

        #Bind
        # pyrefly: ignore [missing-attribute]
        if self.bind.next_turn():
            # pyrefly: ignore [missing-attribute]
            msg += f"{self.name} is no longer bound!\n"
        # pyrefly: ignore [missing-attribute]
        elif self.bind.active() and otherpoke is not None:
            if otherpoke.held_item == "binding-band":
                # pyrefly: ignore [missing-attribute]
                msg += self.damage(self.starting_hp // 6, battle, source=f"{otherpoke.name}'s bind")
            else:
                # pyrefly: ignore [missing-attribute]
                msg += self.damage(self.starting_hp // 8, battle, source=f"{otherpoke.name}'s bind")
        #Ingrain
        # pyrefly: ignore [missing-attribute]
        if self.ingrain:
            heal = self.starting_hp // 16
            # pyrefly: ignore [missing-attribute]
            if self.held_item == "big_root":
                heal = int(heal * 1.3)
            # pyrefly: ignore [missing-attribute]
            msg += self.heal(heal, source="ingrain")
        #Aqua Ring
        # pyrefly: ignore [missing-attribute]
        if self.aqua_ring:
            heal = self.starting_hp // 16
            # pyrefly: ignore [missing-attribute]
            if self.held_item == "big_root":
                heal = int(heal * 1.3)
            # pyrefly: ignore [missing-attribute]
            msg += self.heal(heal, source="aqua ring")
        #Octolock
        # pyrefly: ignore [missing-attribute]
        if self.octolock and otherpoke is not None:
            # pyrefly: ignore [missing-attribute]
            msg += self.append_defense(-1, attacker=self, source=f"{otherpoke.name}'s octolock")
            # pyrefly: ignore [missing-attribute]
            msg += self.append_spdef(-1, attacker=self, source=f"{otherpoke.name}'s octolock")
        #Grassy Terrain
        # pyrefly: ignore [missing-attribute]
        if battle.terrain.item == "grassy" and self.grounded(battle) and not self.heal_block.active():
            # pyrefly: ignore [missing-attribute]
            msg += self.heal(self.starting_hp // 16, source="grassy terrain")

        # Goes at the end so everything in this func that checks it handles it correctly.
        self.swapped_in = False
        # pyrefly: ignore [missing-attribute]
        msg += self.held_item.activate_end_of_turn(battle)
        return msg
