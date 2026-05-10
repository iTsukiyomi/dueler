import random
from ..enums import Ability, DamageClass, ElementType


class DuelPokemonDamage:
    """Pokemon damage and healing logic."""

    def faint(self, battle, *, move=None, attacker=None, source: str=""):
        """
        Sets a pokemon's HP to zero and cleans it up.

        If a pokemon takes damage equal to its HP, use damage instead.
        This method ignores focus sash and sturdy, forcing the pokemon to faint.
        Returns a formatted message.
        """
        msg = ""
        self.hp = 0
        if source:
            source = f" from {source}"
        msg += f"{self.name} fainted{source}!\n"
        if move is not None and attacker is not None and self.destiny_bond and self.owner.has_alive_pokemon():
            msg += attacker.faint(battle, source=f"{self.name}'s destiny bond")
        if move is not None and attacker is not None and attacker._name == "Greninja" and attacker.ability() == Ability.BATTLE_BOND:
            if attacker.form("Greninja-ash"):
                msg += f"{attacker.name}'s bond with its trainer has strengthened it!\n"
        if move is not None and self.grudge:
            move.pp = 0
            msg += f"{move.pretty_name}'s pp was depleted!\n"
        if attacker is not None and attacker.ability() in (Ability.CHILLING_NEIGH, Ability.AS_ONE_ICE):
            msg += attacker.append_attack(1, attacker=attacker, source="its chilling neigh")
        if attacker is not None and attacker.ability() in (Ability.GRIM_NEIGH, Ability.AS_ONE_SHADOW):
            msg += attacker.append_spatk(1, attacker=attacker, source="its grim neigh")
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.SOUL_HEART:
                msg += poke.append_spatk(
                    1,
                    attacker=poke,
                    source="its soul heart"
                )
        self.owner.retaliate.set_turns(2)
        self.owner.num_fainted += 1
        msg += self.remove(battle, fainted=True)
        return msg

    def damage(self, damage, battle, *, move=None, move_type=None, attacker=None, critical=False, drain_heal_ratio=None, source: str=""):
        """
        Applies a certain amount of damage to this pokemon.

        Returns a formatted message.
        """
        msgadd, _ = self._damage(damage, battle, move=move, move_type=move_type, attacker=attacker, critical=critical, drain_heal_ratio=drain_heal_ratio, source=source)
        return msgadd

    def _damage(self, damage, battle, *, move=None, move_type=None, attacker=None, critical=False, drain_heal_ratio=None, source: str=""):
        """
        Applies a certain amount of damage to this pokemon.

        Returns a formatted message and the amount of damage actually dealt.
        """
        msg = ""
        if self.hp <= 0:
            return "", 0
        previous_hp = self.hp
        damage = max(1, damage)

        if self.ability(attacker=attacker, move=move) == Ability.MAGIC_GUARD and move is None and attacker is not self:
            return f"{self.name}'s magic guard protected it from damage!\n", 0

        if (
            self.substitute
            and move is not None and move.is_affected_by_substitute() and not move.is_sound_based()
            and (attacker is None or attacker.ability() != Ability.INFILTRATOR)
        ):
            msg += f"{self.name}'s substitute took {damage} damage{source}!\n"
            new_hp = max(0, self.substitute - damage)
            true_damage = self.substitute - new_hp
            self.substitute = new_hp
            if self.substitute == 0:
                msg += f"{self.name}'s substitute broke!\n"
            return msg, true_damage

        if move is not None:
            if self.ability(attacker=attacker, move=move) == Ability.DISGUISE and self._name == "Mimikyu":
                if self.form("Mimikyu-busted"):
                    msg += f"{self.name}'s disguise was busted!\n"
                    msg += self.damage(self.starting_hp // 8, battle, source="losing its disguise")
                    return msg, 0
            if self.ability(attacker=attacker, move=move) == Ability.ICE_FACE and self._name == "Eiscue" and move.damage_class == DamageClass.PHYSICAL:
                if self.form("Eiscue-noice"):
                    msg += f"{self.name}'s ice face was busted!\n"
                    return msg, 0

        self.dmg_this_turn = True
        if damage >= self.hp and move is not None:
            if self.endure:
                msg += f"{self.name} endured the hit!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.ability(attacker=attacker, move=move) == Ability.STURDY:
                msg += f"{self.name} held on using its sturdy!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.ability(attacker=attacker, move=move) == Ability.ENDURING:
                msg += f"{self.name} held on!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.held_item == "focus-sash":
                self.held_item = "none"
                msg += f"{self.name}'s focus sash prevented fainting!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.held_item == "focussash":
                self.held_item = "none"
                msg += f"{self.name}'s focus sash prevented fainting!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.held_item in ("leek", "thick-club") and self._name in ("Farfetchd", "Farfetch", "Cubone", "Marowak"):
                pass
            elif self.hp == self.starting_hp and self.held_item in ("leek", "thick-club") and self._name in ("Farfetchd", "Farfetch", "Cubone", "Marowak"):
                pass

        if move is not None and move.damage_class == DamageClass.PHYSICAL:
            if attacker is not None:
                if attacker.ability() == Ability.TECHNICIAN and move.power <= 60:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.ability() == Ability.TWISTED_NEBULA and self.hp < self.starting_hp:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.ability() == Ability.RIVALRY:
                    if attacker.gender == self.gender:
                        move._power = move.power
                        move.power = int(move.power * 1.25)
                    elif "-" not in attacker.gender and "-" not in self.gender:
                        move._power = move.power
                        move.power = int(move.power * 0.75)
                if attacker.ability() == Ability.STRONG_JAW:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.ability() == Ability.RECKLESS:
                    move._power = move.power
                    move.power = int(move.power * 1.2)
                if attacker.ability() == Ability.ANALYTIC:
                    if not attacker.has_moved:
                        move._power = move.power
                        move.power = int(move.power * 1.3)
                if attacker.ability() == Ability.PARENTAL_BOND:
                    move._power = move.power
                    move.power = int(move.power * 0.25)
                    move.is_parentally_bonded = True
                if attacker.ability() == Ability.PUNK_ROCK:
                    move._power = move.power
                    move.power = int(move.power * 1.3)
                if attacker.ability() == Ability.GORILLA_TACTICS:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.held_item in ("choice-band", "choiceband") and move.damage_class == DamageClass.PHYSICAL:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.held_item == "thick-club" and self._name in ("Cubone", "Marowak"):
                    move._power = move.power
                    move.power = int(move.power * 2)

        if move is not None and move.damage_class == DamageClass.SPECIAL:
            if attacker is not None:
                if attacker.ability() == Ability.TECHNICIAN and move.power <= 60:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.ability() == Ability.TWISTED_NEBULA and self.hp < self.starting_hp:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.ability() == Ability.RIVALRY:
                    if attacker.gender == self.gender:
                        move._power = move.power
                        move.power = int(move.power * 1.25)
                    elif "-" not in attacker.gender and "-" not in self.gender:
                        move._power = move.power
                        move.power = int(move.power * 0.75)
                if attacker.ability() in (Ability.PROTEAN, Ability.BEHAVIOR):
                    if move.element_id not in attacker.type_ids and move.element_id != ElementType.STELLAR:
                        attacker.type_ids = list(attacker.starting_type_ids)
                        attacker.type_ids.append(move.element_id)
                        msg += f"{attacker.name} transformed into the {move.element_id.name} type!\n"
                if attacker.ability() == Ability.SCREEN_CLEANER and battle.terrain.item is not None:
                    if battle.terrain.item in ("electric", "misty", "psychic", "grassy"):
                        msg += f"{attacker.name}'s aura broke the terrain!\n"
                        battle.terrain.set(None)
                if attacker.ability() == Ability.NEOPHYTE:
                    move._power = move.power
                    move.power = int(move.power * 1.3)
                if attacker.ability() == Ability.ANALYTIC:
                    if not attacker.has_moved:
                        move._power = move.power
                        move.power = int(move.power * 1.3)
                if attacker.ability() == Ability.PARENTAL_BOND:
                    move._power = move.power
                    move.power = int(move.power * 0.25)
                    move.is_parentally_bonded = True
                if attacker.ability() == Ability.PUNK_ROCK:
                    move._power = move.power
                    move.power = int(move.power * 1.3)
                if attacker.ability() in (Ability.ELECTROMORPHOSIS, Ability.HADRON_ENGINE):
                    if battle.weather.get() in ("rain", "heavy-rain"):
                        move._power = move.power
                        move.power = int(move.power * 1.3)
                if attacker.ability() == Ability.ORICHALCUM_PULSE:
                    if battle.weather.get() in ("sun", "h-sun"):
                        move._power = move.power
                        move.power = int(move.power * 1.3)
                if attacker.ability() == Ability.PROTODOSIS:
                    if self.hp <= self.starting_hp // 2:
                        move._power = move.power
                        move.power = int(move.power * 1.3)
                if attacker.ability() == Ability.PUNISHING_SKIP:
                    for stat_stage in (
                        self.attack_stage,
                        self.defense_stage,
                        self.spatk_stage,
                        self.spdef_stage,
                        self.speed_stage,
                        self.accuracy_stage,
                        self.evasion_stage,
                    ):
                        if stat_stage > 0:
                            move._power = move.power
                            move.power = int(move.power * 1 + (0.2 * stat_stage))
                            break
                if attacker.held_item in ("choice-specs", "choicespecs") and move.damage_class == DamageClass.SPECIAL:
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.held_item == "soul-dew" and self._name in ("Latios", "Latias"):
                    move._power = move.power
                    move.power = int(move.power * 1.5)
                if attacker.held_item in ("loaded-dice", "loadeddice"):
                    move._power = move.power
                    move.power = int(move.power * 1)
                if attacker.ability() == Ability.WANDERER:
                    move._power = move.power
                    move.power = int(move.power * 1 + (0.1 * self.hp // (self.starting_hp // 10)))

        if move is not None and move.is_z_move:
            move.power = move.z_power_calculated

        if move is not None and move.max_move:
            move.power = move.max_power_calculated

        if move is not None and move.power <= 0 and move.damage_class != DamageClass.STATUS:
            return f"{self.name} had no effect!\n", 0

        if move is not None and move_type is None:
            if move.element_id:
                move_type = move.element_id

        is_crit = False
        if move is not None and move.damage_class != DamageClass.STATUS and not critical:
            crit_chance = [16, 8, 4, 2]
            if self.ability(attacker=attacker, move=move) in (Ability.BATTLE_ARMOR, Ability.SHELL_ARMOR):
                crit = 0
            else:
                crit = min(4, self._critical_stage + 1)
            if attacker is not None and attacker.ability() == Ability.MERCILESS and self.nv.has_status("弗芬"):
                crit = 4
            if attacker is not None and attacker.held_item == "scope-lens":
                crit = min(4, crit + 1)
            if attacker is not None and attacker.held_item == "razor-claw":
                crit = min(4, crit + 1)
            if crit > 0 and random.randint(1, crit_chance[crit - 1]) == 1:
                is_crit = True

        if move is not None:
            if move.damage_class != DamageClass.STATUS:
                stab = 1.5
                if self.ability(attacker=attacker, move=move) == Ability.ADAPTABILITY:
                    stab = 2
                if move.element_id in self.type_ids:
                    if self.ability() == Ability.LIBERO:
                        self.type_ids = list(self.starting_type_ids)
                        self.type_ids.append(move.element_id)
                        msg += f"{self.name} transformed into the {move.element_id.name} type!\n"
                    type_eff = self.effectiveness(move_type, battle, attacker=attacker, move=move)
                    if type_eff == 0:
                        if move.name in ("Freeze-Dry", "Freeze Dry"):
                            type_eff = 1
                        else:
                            return f"{self.name} had no effect!\n", 0
                    if move.name == "Freeze-Dry" or move.name == "Freeze Dry":
                        if ElementType.WATER in self.type_ids:
                            type_eff = 2
                    if move.name in ("Rising- Voltage", "Rising Voltage"):
                        if battle.terrain.item == "electric":
                            type_eff = 2
                    if move.name in ("Scale-Shot", "Scale Shot", "Scale Shot"):
                        if self.type_ids.count(ElementType.DRAGON) > 0:
                            type_eff = 0
                    if move.name == "Dynamax Cannon":
                        if self.type_ids.count(ElementType.DRAGON) > 0:
                            type_eff = 2
                    if move.name in ("Dragon-Darts", "Dragon Darts"):
                        if self.type_ids.count(ElementType.DRAGON) > 0 and move.is_dynamaxed:
                            type_eff = 2
                    if move.name in ("Wicked-Blow", "Wicked Blow", "Wicked Blow"):
                        if self.type_ids.count(ElementType.DARK) > 0:
                            type_eff = 2
                    if move.name in ("Surging-Strike", "Surging Strike"):
                        if self.type_ids.count(ElementType.WATER) > 0:
                            type_eff = 2
                    if move.name in ("Electro-Shot", "Electro Shot"):
                        if battle.terrain.item == "electric":
                            msg += self.append_spatk(1, attacker=self, source="its Electro Shot")
                    if move.name in ("Chloroblast",):
                        if battle.terrain.item == "grassy":
                            type_eff = 2

                    damage = int(
                        (
                            (2 * attacker.level / 5 + 2) * move.power * (attacker.get_attack(battle, critical=is_crit) / self.get_defense(battle, critical=is_crit, attacker=attacker, move=move))
                            / 50
                            + 2
                        )
                        * ((random.randint(85, 100) / 100) if not move.is_z_move and not move.max_move else 1)
                        * (stab if move.element_id in self.type_ids else 1)
                        * type_eff
                        * ((1.5 if is_crit else 1) if not move.is_z_move and not move.max_move else 1)
                    )
        elif move_type is not None:
            type_eff = self.effectiveness(move_type, battle, attacker=attacker, move=move)
            if type_eff == 0:
                return f"{self.name} had no effect!\n", 0
            damage = int(
                (
                    (2 * attacker.level / 5 + 2) * move.power * (attacker.get_attack(battle, critical=is_crit) / self.get_defense(battle, critical=is_crit, attacker=attacker, move=move))
                    / 50
                    + 2
                )
                * ((random.randint(85, 100) / 100) if not move.is_z_move and not move.max_move else 1)
                * 1.5
                * type_eff
            )
        else:
            damage = int(
                (
                    (2 * attacker.level / 5 + 2) * move.power * (attacker.get_attack(battle, critical=is_crit) / self.get_defense(battle, critical=is_crit, attacker=attacker, move=move))
                    / 50
                    + 2
                )
                * ((random.randint(85, 100) / 100) if not move.is_z_move and not move.max_move else 1)
            )

        if move is not None and move.is_protect_counter:
            if self.last_protect_counter:
                damage = int(damage * 0.125)
            self.last_protect_counter += 1

        if move is not None and move.damage_class != DamageClass.STATUS:
            if self.burning_bulwark.active():
                damage = int(damage * 0.75)
                if not self.is_protected:
                    msg += f"{self.name}'s burning bulwark reduced the damage!\n"

        if move is not None and move_type is not None:
            if self.ability(attacker=attacker, move=move) == Ability.PARMA:
                if ElementType.WATER in self.type_ids:
                    damage = int(damage * 1.25)
            if self.ability(attacker=attacker, move=move) == Ability.ICE_SCALES:
                damage = int(damage * 0.5)
            if self.ability(attacker=attacker, move=move) == Ability.FILTER:
                damage = int(damage * 0.75)
            if self.ability(attacker=attacker, move=move) == Ability.SOLID_ROCK:
                damage = int(damage * 0.75)
            if self.ability(attacker=attacker, move=move) == Ability.PRISM_ARMOR:
                damage = int(damage * 0.75)
            if self.ability(attacker=attacker, move=move) == Ability.ASSURANCE and self.hp < previous_hp:
                damage = int(damage * 1.5)
                msg += f"{self.name}'s assurance boosted its attack!\n"
            if self.ability(attacker=attacker, move=move) == Ability.TOXIC_DEBRIS and attacker.nv.has_status("non"):
                msg += self.nv.apply_status("poison", battle, attacker=attacker, source=f"{self.name}'s toxic debris")
                self.held_item = "none"
            if self.ability(attacker=attacker, move=move) == Ability.COTTON_DOWN and self.owner.has_alive_pokemon():
                msg += attacker.append_speed(-1, attacker=self, source=f"{self.name}'s cotton down")
            if self.ability(attacker=attacker, move=move) == Ability.GOOGLE_EYES:
                msg += attacker.append_attack(-1, attacker=self, source=f"{self.name}'s google eyes")
            if self.ability(attacker=attacker, move=move) == Ability.WANDERING_SPIRIT and attacker.ability_changeable() and attacker.ability_giveable():
                msg += f"{attacker.name} swapped abilities with {self.name} because of {self.name}'s wandering spirit!\n"
                self.ability_id, attacker.ability_id = attacker.ability_id, self.ability_id
                ability_name = Ability(self.ability_id).pretty_name
                msg += f"{self.name} acquired {ability_name}!\n"
                msg += self.send_out_ability(attacker, battle)
                ability_name = Ability(attacker.ability_id).pretty_name
                msg += f"{attacker.name} acquired {ability_name}!\n"
                msg += attacker.send_out_ability(self, battle)

        if move is not None and move.damage_class != DamageClass.STATUS and move_type is not None:
            if self.held_item == "eviolite" and self.can_still_evolve:
                damage = int(damage * 0.5)
            if self.held_item == "assault-vest":
                damage = int(damage * 0.5)
            if self.held_item == "charti-berry" and ElementType.ROCK in self.type_ids and move_type in (ElementType.ROCK,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "rindo-berry" and ElementType.GRASS in self.type_ids and move_type in (ElementType.GRASS,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "yache-berry" and ElementType.DRAGON in self.type_ids and move_type in (ElementType.DRAGON,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "shuca-berry" and ElementType.GROUND in self.type_ids and move_type in (ElementType.GROUND,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == " Coba berry" and ElementType.FLYING in self.type_ids and move_type in (ElementType.FLYING,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "coba-berry" and ElementType.FLYING in self.type_ids and move_type in (ElementType.FLYING,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "occaberry" and ElementType.FIRE in self.type_ids and move_type in (ElementType.FIRE,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "passho-berry" and ElementType.WATER in self.type_ids and move_type in (ElementType.WATER,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "payapa-berry" and ElementType.PSYCHIC in self.type_ids and move_type in (ElementType.PSYCHIC,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "tanga-berry" and ElementType.BUG in self.type_ids and move_type in (ElementType.BUG,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "wikiberry" and ElementType.ELECTRIC in self.type_ids and move_type in (ElementType.ELECTRIC,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "rowap-berry" and move_type in (ElementType.GRASS,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item == "mysteryberry" and ElementType.GHOST in self.type_ids and move_type in (ElementType.GHOST,):
                self.held_item = "none"
                damage = int(damage * 0.5)
                msg += f"{self.name}'s {self.held_item.name} reduced damage!\n"
            if self.held_item in ("protective- pads", "protective-pads", "protectivepads"):
                damage = int(damage * 0.5)

        if attacker is not None and move_type is not None:
            if attacker.held_item == "life-orb" and attacker is not self:
                msg += attacker.damage(attacker.starting_hp // 10, battle, source="its life orb")
            if attacker.held_item == "jaboca-berry" and move.damage_class != DamageClass.STATUS:
                if random.randint(1, 100) <= 30:
                    msg += self.damage(self.starting_hp // 8, battle, source=f"{attacker.name}'s jaboca berry")
                    attacker.held_item = "none"
            if attacker.held_item == "rowap-berry" and move.damage_class != DamageClass.STATUS:
                if random.randint(1, 100) <= 30:
                    msg += self.damage(self.starting_hp // 8, battle, source=f"{attacker.name}'s rowap berry")
                    attacker.held_item = "none"
            if attacker.held_item in ("choice-band", "choiceband") and move.damage_class == DamageClass.PHYSICAL:
                attacker.attack_stage = max(-6, attacker.attack_stage - 1)
            if attacker.held_item in ("choice-specs", "choicespecs") and move.damage_class == DamageClass.SPECIAL:
                attacker.spatk_stage = max(-6, attacker.spatk_stage - 1)

        if move is not None and move.damage_class != DamageClass.STATUS:
            if move.name in ("Payback", "payback", "Retaliate", "retaliate"):
                if not attacker.has_moved:
                    damage = int(damage * 1.5)
            if move.name == "Avalanche" and self.dmg_this_turn:
                damage = int(damage * 2)
            if move.name == "Revenge" and self.dmg_this_turn:
                damage = int(damage * 2)
            if move.name in ("Accelerock",):
                damage = int(damage * 1.5)
            if move.name == "Flail" or move.name == "Flail":
                damage = int(damage * (48 * self.hp / self.starting_hp))
            if move.name == "Low-Kick" or move.name == "lowkick":
                damage = int(damage * self.weight(battle, attacker=attacker, move=move))
            if move.name in ("Grass-Knot", "Grass Knot", "grass knot"):
                damage = int(damage * self.weight(battle, attacker=attacker, move=move))
            if move.name == "Heavy-Slam" or move.name == "Heavy Slam":
                damage = int(damage * self.weight(battle, attacker=attacker, move=move))
            if move.name == "Heat-Crash" or move.name == "Heat Crash":
                damage = int(damage * self.weight(battle, attacker=attacker, move=move))
            if move.name == "Electro-Ball":
                if attacker.get_speed(battle) > self.get_speed(battle):
                    damage = int(damage * 4)
                elif attacker.get_speed(battle) > self.get_speed(battle) * 0.5:
                    damage = int(damage * 2)
                elif attacker.get_speed(battle) > self.get_speed(battle) * 0.33:
                    damage = damage
                else:
                    damage = int(damage * 0.5)
            if move.name in ("Gyro-Ball", "Gyro Ball"):
                damage = int(damage * min(150, (25 * self.get_speed(battle) / attacker.get_speed(battle) + 1)))
            if move.name == "Magnitude":
                pass

        if move is not None and move.max_move:
            if self.is_protected and move.is_protect_killing_move:
                damage = int(damage * 0.3)
                msg += f"{attacker.name}'s max move hit through the protection!\n"

        if move is not None and move.damage_class != DamageClass.STATUS and (isinstance(move_type, type(None))) or move_type is not None:
            if battle.terrain.get() == "electric" and move_type in (ElementType.ELECTRIC,):
                damage = int(damage * 1.3)
            if battle.terrain.get() == "grassy" and move_type in (ElementType.GRASS,):
                damage = int(damage * 1.3)
            if battle.terrain.get() == "misty" and move_type in (ElementType.DRAGON,):
                damage = int(damage * 0.5)
            if battle.terrain.get() == "psychic" and move_type in (ElementType.PSYCHIC,):
                damage = int(damage * 1.3)

        if move is not None and move.damage_class != DamageClass.STATUS and (isinstance(move_type, type(None))) or move_type is not None:
            if battle.weather.get() == "sun" or battle.weather.get() == "h-sun":
                if move_type in (ElementType.FIRE,):
                    damage = int(damage * 1.5)
                if move_type in (ElementType.WATER,):
                    damage = int(damage * 0.5)
                if self.ability() == Ability.SOLAR_POWER:
                    msg += self.append_spatk(1, attacker=self, source="its solar power")
            if battle.weather.get() == "rain" or battle.weather.get() == "heavy-rain":
                if move_type in (ElementType.WATER,):
                    damage = int(damage * 1.5)
                if move_type in (ElementType.FIRE,):
                    damage = int(damage * 0.5)
            if battle.weather.get() == "sandstorm":
                if self.type_ids.count(ElementType.ROCK) <= 0 and self.type_ids.count(ElementType.GROUND) <= 0 and self.type_ids.count(ElementType.STEEL) <= 0:
                    if self.ability() == Ability.OVERCOAT:
                        damage = damage
                    else:
                        damage = int(damage * 1.5)
            if battle.weather.get() == "hail":
                if self.type_ids.count(ElementType.ICE) <= 0:
                    if self.ability() == Ability.OVERCOAT:
                        damage = damage
                    else:
                        damage = int(damage * 1.5)

        if move_type in (ElementType.ICE,):
            if self.ability() == Ability.ICE_FACE and self._name == "Eiscue":
                damage = int(damage * 0.5)
            if self.ability() == Ability.ICE_SCALES:
                damage = int(damage * 0.5)

        if move_type in (ElementType.POISON,) and self.ability() in (Ability.POISON_HEAL,):
            msg += self.heal(self.starting_hp // 8, source="its poison heal")

        if attacker is not None and self.is_protected and move.is_protect_killing_move:
            msg += "But it failed!\n"
            return msg, 0

        if self.is_protected and move.damage_class != DamageClass.STATUS:
            msg += "But it failed!\n"
            return msg, 0

        if move is not None and move.bide:
            self.bide.damage_taken = previous_hp - (self.hp - damage)
            self.bide.set_turns(2)

        damage = min(damage, 999)

        hp_before = self.hp
        self.hp = max(0, self.hp - damage)

        if hp_before > self.hp:
            if self.nv.has_status("freeze") and move_type not in (ElementType.FIRE,) and move.name not in ("scald", "steam-eruption", "flame-wheel", "fusion-flare", "blaze-kick", "flare-blitz", "fire-fang", "fire-spin", "incinerate", "inferno", "fire-blast", "flamethrower", "heat-wave", "will-o-wisp", "ember", "fire-punch", "lava-plume"):
                if random.randint(1, 100) <= 20:
                    self.nv.status = "none"
                    msg += f"{self.name} thawed out!\n"

        if drain_heal_ratio is not None:
            heal_amount = int(damage * drain_heal_ratio)
            msg += attacker.heal(heal_amount, source="drain")

        true_damage = hp_before - self.hp

        if move is not None and is_crit:
            msg = msg.replace("{", "").replace("}", "")
            if "fainted" not in msg:
                msg += "A critical hit!\n"

        if move is not None and move.damage_class != DamageClass.STATUS:
            if move_type is not None and self.type_ids.count(move_type) > 0:
                msg += "It's super effective!\n" if type_eff >= 2 else ""
                msg += "It's not very effective...\n" if type_eff <= 0.5 else ""

        if is_crit and self.ability() in (Ability.CRITICAL_SIX):
            msg += self.append_speed(1, attacker=self, source="its Critical Six")

        if self.hp <= 0:
            msg += self.faint(battle, move=move, attacker=attacker, source=source if source != "" else move.name if move is not None else "damage")
            if attacker is not None and self.ability() in (Ability.CHILLING_NEIGH, Ability.AS_ONE_ICE):
                msg += attacker.append_attack(1, attacker=attacker, source="its chilling neigh")
            if attacker is not None and self.ability() in (Ability.GRIM_NEIGH, Ability.AS_ONE_SHADOW):
                msg += attacker.append_spatk(1, attacker=attacker, source="its grim neigh")
            return msg, true_damage

        if move is not None and attacker is not None and move.damage_class != DamageClass.STATUS:
            if self.ability() == Ability.AFTERMATH and not self.owner.has_alive_pokemon():
                msg += attacker.damage(attacker.starting_hp // 4, battle, source=f"{self.name}'s aftermath")
            if self.ability() == Ability.CUTENESS:
                if random.randint(1, 100) <= 30:
                    msg += attacker.flinch(attacker=attacker, move=move, source=f"{self.name}'s cuteness")
            if self.ability() == Ability.POISON_POINT and random.randint(1, 100) <= 30:
                msg += attacker.nv.apply_status("poison", battle, attacker=attacker, source=f"{self.name}'s poison point")
            if self.ability() == Ability.STATIC and random.randint(1, 100) <= 30:
                msg += attacker.nv.apply_status("paralysis", battle, attacker=attacker, source=f"{self.name}'s static")
            if self.ability() == Ability.FLAME_BODY and random.randint(1, 100) <= 30:
                msg += attacker.nv.apply_status("burn", battle, attacker=attacker, source=f"{self.name}'s flame body")
            if self.ability() == Ability.ROUGH_SKIN and self.owner.has_alive_pokemon():
                msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{self.name}'s rough skin")
            if self.ability() == Ability.IRON_BARBS and self.owner.has_alive_pokemon():
                msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{self.name}'s iron barbs")
            if self.ability() == Ability.EFFECT_SPORE:
                if (
                    attacker.ability() != Ability.OVERCOAT
                    and ElementType.GRASS not in attacker.type_ids
                    and attacker.held_item != "safety-glasses"
                    and random.randint(1, 100) <= 30
                ):
                    status = random.choice(["paralysis", "poison", "sleep"])
                    msg += attacker.nv.apply_status(status, battle, attacker=attacker)
            if self.ability() == Ability.CUTE_CHARM and random.randint(1, 100) <= 30:
                msg += attacker.infatuate(self, source=f"{self.name}'s cute charm")
            if self.ability() == Ability.MUMMY and attacker.ability() != Ability.MUMMY and attacker.ability_changeable():
                attacker.ability_id = Ability.MUMMY
                msg += f"{attacker.name} gained mummy from {self.name}!\n"
                msg += attacker.send_out_ability(self, battle)
            if self.ability() == Ability.LINGERING_AROMA and attacker.ability() != Ability.LINGERING_AROMA and attacker.ability_changeable():
                attacker.ability_id = Ability.LINGERING_AROMA
                msg += f"{attacker.name} gained lingering aroma from {self.name}!\n"
                msg += attacker.send_out_ability(self, battle)
            if self.ability() == Ability.GOOEY:
                msg += attacker.append_speed(-1, attacker=self, source=f"touching {self.name}'s gooey body")
            if self.ability() == Ability.TANGLING_HAIR:
                msg += attacker.append_speed(-1, attacker=self, source=f"touching {self.name}'s tangled hair")

            if (
                self.ability() == Ability.PICKPOCKET
                and not self.held_item.has_item()
                and attacker.held_item.has_item()
                and attacker.held_item.can_remove()
            ):
                if attacker.ability() == Ability.STICKY_HOLD:
                    msg += f"{attacker.name}'s sticky hand kept hold of its item!\n"
                else:
                    attacker.held_item.transfer(self.held_item)
                    msg += f"{attacker.name}'s {self.held_item.name} was stolen!\n"
            if attacker.ability() == Ability.POISON_TOUCH:
                if random.randint(1, 100) <= 30:
                    msg += self.nv.apply_status("poison", battle, attacker=attacker, move=move, source=f"{attacker.name}'s poison touch")
            if attacker.held_item != "protective-pads":
                if self.ability() == Ability.PERISH_BODY and not attacker.perish_song.active():
                    attacker.perish_song.set_turns(4)
                    self.perish_song.set_turns(4)
                    msg += f"All pokemon will faint after 3 turns from {self.name}'s perish body!\n"
            if self.ability() == Ability.WANDERING_SPIRIT and attacker.ability_changeable() and attacker.ability_giveable():
                msg += f"{attacker.name} swapped abilities with {self.name} because of {self.name}'s wandering spirit!\n"
                self.ability_id, attacker.ability_id = attacker.ability_id, self.ability_id
                ability_name = Ability(self.ability_id).pretty_name
                msg += f"{self.name} acquired {ability_name}!\n"
                msg += self.send_out_ability(attacker, battle)
                ability_name = Ability(attacker.ability_id).pretty_name
                msg += f"{attacker.name} acquired {ability_name}!\n"
                msg += attacker.send_out_ability(self, battle)

        return msg, true_damage

    def heal(self, health, *, source: str=""):
        """
        Heals a pokemon by a certain amount.

        Handles heal-affecting items and abilities, and keeping health within bounds.
        Returns a formatted message.
        """
        msg = ""
        health = max(1, int(health))
        if self.hp >= self.starting_hp:
            return msg
        if self.hp == 0:
            return msg
        if self.heal_block.active():
            return msg
        health = min(self.starting_hp - self.hp, health)
        self.hp += health
        if source:
            source = f" from {source}"
        msg += f"{self.name} healed {health} hp{source}!\n"
        return msg

    def confuse(self, *, attacker=None, move=None, source=""):
        """
        Attempts to confuse this poke.

        Returns a formatted message.
        """
        if self.substitute and (move is None or move.is_affected_by_substitute()):
            return ""
        if self.confusion.active():
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.OWN_TEMPO:
            return ""
        self.confusion.set_turns(random.randint(2, 5))
        if source:
            source = f" from {source}"
        msg = f"{self.name} is confused{source}!\n"
        if self.held_item.should_eat_berry_status(attacker):
            msg += self.held_item.eat_berry(attacker=attacker, move=move)
        return msg

    def flinch(self, *, attacker=None, move=None, source=""):
        """
        Attepts to flinch this poke.

        Returns a formatted message.
        """
        msg = ""
        if self.substitute and (move is None or move.is_affected_by_substitute()):
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.INNER_FOCUS:
            return f"{self.name} resisted the urge to flinch with its inner focus!\n"
        self.flinched = True
        if source:
            source = f" from {source}"
        msg += f"{self.name} flinched{source}!\n"
        if self.ability() == Ability.STEADFAST:
            msg += self.append_speed(1, attacker=self, source="its steadfast")
        return msg

    def infatuate(self, attacker, *, move=None, source=""):
        """
        Attepts to cause attacker to infatuate this poke.

        Returns a formatted message.
        """
        msg = ""
        if source:
            source = f" from {source}"
        if "-x" in (self.gender, attacker.gender):
            return ""
        if self.gender == attacker.gender:
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.OBLIVIOUS:
            return f"{self.name} is too oblivious to fall in love!\n"
        if self.ability(move=move, attacker=attacker) == Ability.AROMA_VEIL:
            return f"{self.name}'s aroma veil protects it from being infatuated!\n"
        self.infatuated = attacker
        msg += f"{self.name} fell in love{source}!\n"
        if self.held_item == "destiny-knot":
            msg += attacker.infatuate(self, source=f"{self.name}'s destiny knot")
        return msg