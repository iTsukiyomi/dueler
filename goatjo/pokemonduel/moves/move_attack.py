import random
from ..enums import Ability, DamageClass, ElementType


class MoveAttack:
    """Attack calculation and execution."""

    def attack(self, attacker, defender, battle):
        """Attacks the defender using this move."""
        from ..enums import MoveTarget

        msg = ""
        current_type = self.get_type(attacker, defender, battle)

        effectiveness = defender.effectiveness(current_type, battle, attacker=attacker, move=self)
        if self.effect == 338:
            effectiveness *= defender.effectiveness(ElementType.FLYING, battle, attacker=attacker, move=self)
        if effectiveness <= 0:
            return ("The attack had no effect!\n", 0)
        if effectiveness <= .5:
            msg += "It's not very effective...\n"
        elif effectiveness >= 2:
            msg += "It's super effective!\n"

        parental_bond = False
        min_hits = self.min_hits
        max_hits = self.max_hits
        if self.effect == 361 and attacker._name == "Greninja-ash":
            min_hits = 1
            max_hits = 1
        elif self.effect == 304:
            min_hits = 3
            max_hits = 3
        elif self.effect == 518:
            min_hits = 2
            max_hits = 5
        elif attacker.ability() == Ability.SKILL_LINK and min_hits > 1:
            min_hits = max_hits

        numhits = random.randint(min_hits, max_hits)
        if self.effect == 226:
            numhits = 1

        if numhits > 1 and self.id not in (681, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708, 709):
            msg += f"Hit {numhits} time(s)!\n"

        for hit in range(numhits):
            if hit == 1 and attacker.ability() == Ability.PARENTAL_BOND and not parental_bond and max_hits > 1:
                parental_bond = True

            is_protect_counter = False
            if hit > 0:
                if defender.protect_counter >= 3:
                    msg += "But it failed to hit!\n"
                    break
                is_protect_counter = True

            damage, critical, is_super_effective, is_not_very_effective = self.calculate_damage(
                attacker, defender, battle, current_type, effectiveness, is_protect_counter
            )

            if defender.ability(attacker=attacker, move=self) == Ability.STURDY and defender.hp == defender.starting_hp:
                damage = 0
                msg += f"{defender.name} is protected by Sturdy!\n"

            if defender.ability(attacker=attacker, move=self) == Ability.ICE_FACE and defender._name == "Eiscue" and self.damage_class == DamageClass.PHYSICAL:
                if defender.form("Eiscue"):
                    damage = 0
                    msg += f"{defender.name}'s Ice Face blocked the attack!\n"

            if defender.ability(attacker=attacker, move=self) == Ability.ICE_SCALES and self.damage_class == DamageClass.SPECIAL:
                damage //= 2
                msg += f"{defender.name}'s Ice Scales reduced the damage!\n"

            if defender.ability(attacker=attacker, move=self) == Ability.PASTEL_VEIL and defender.nv.poison():
                damage //= 2

            if defender.held_item.get_defensive_multiplier(current_type, is_super_effective) != 1.0:
                msg += f"{defender.name}'s {defender.held_item} reduced the damage!\n"

            if is_protect_counter:
                defender.protect_counter += 1
            else:
                defender.protect_counter = 0

            defender.used_damaging_move_this_turn = True

            self.apply_damage(attacker, defender, battle, damage, current_type, critical, msg)

            if defender.hp <= 0:
                break

        return msg, numhits

    def calculate_damage(self, attacker, defender, battle, current_type, effectiveness, is_protect_counter):
        """Calculate damage dealt by the move."""
        power = self.get_power(attacker, defender, battle)
        if power == 0:
            return 0, False, False, False

        from ..enums import MoveTarget

        is_super_effective = effectiveness >= 2
        is_not_very_effective = effectiveness <= 0.5
        critical = False

        level = attacker.level
        if attacker.ability() == Ability.DEBUG:
            level = 100

        if self.id == 573 and attacker.ability() == Ability.ORDINARY:
            level *= 2

        attack_stat = attacker.get_attack()
        defense_stat = defender.get_defense()

        if self.damage_class == DamageClass.SPECIAL:
            attack_stat = attacker.get_spatk()
            defense_stat = defender.get_spdef()

        if self.effect == 222:
            if self.damage_class == DamageClass.PHYSICAL:
                attack_stat = attacker.get_spatk()
            else:
                defense_stat = defender.get_defense()

        if attacker.ability() == Ability.UNIBLOW:
            attack_stat *= 1.5
        if defender.ability() == Ability.UNIBLOW:
            defense_stat *= 1.5

        if attacker.terrain.item == "terrain-extender" and battle.terrain.item:
            pass
        elif battle.terrain.item and self.target in (MoveTarget.USERS_FIELD, MoveTarget.ENTIRE_FIELD, MoveTarget.USER):
            attack_stat = attacker.get_attack()
            if self.damage_class == DamageClass.SPECIAL:
                attack_stat = attacker.get_spatk()
            defense_stat = defender.get_defense()
            if self.damage_class == DamageClass.SPECIAL:
                defense_stat = defender.get_spdef()

        base_damage = (((2 * level) // 5) + 2) * power * (attack_stat // defense_stat)

        if self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
            if attacker.terrain.item != "terrain-extender" and battle.terrain.active():
                base_damage //= 2

            if battle.trick_room.active() or battle.wonder_room.active():
                base_damage *= 2

            if attacker.ability() == Ability.TRANSPARENT:
                base_damage *= 4

            if attacker.terrain.item != "terrain-extender" and battle.terrain.active():
                pass
            elif battle.terrain.active():
                if battle.terrain.item == "electric" and current_type == ElementType.ELECTRIC:
                    base_damage *= 1.3
                elif battle.terrain.item == "grassy" and current_type == ElementType.GRASS:
                    base_damage *= 1.3
                elif battle.terrain.item == "misty" and current_type == ElementType.FAIRY:
                    base_damage *= 1.3
                elif battle.terrain.item == "psychic" and current_type == ElementType.PSYCHIC:
                    base_damage *= 1.3

            if attacker.held_item.get_damage_multiplier(current_type, attacker=attacker, move=self, is_super_effective=is_super_effective, is_not_very_effective=is_not_very_effective) != 1.0:
                base_damage = int(base_damage * attacker.held_item.get_damage_multiplier(current_type, attacker=attacker, move=self, is_super_effective=is_super_effective, is_not_very_effective=is_not_very_effective))

            if attacker.ability() == Ability.AERILATE and current_type == ElementType.FLYING:
                base_damage = int(base_damage * 1.2)
            elif attacker.ability() == Ability.GALVANIZE and current_type == ElementType.ELECTRIC:
                base_damage = int(base_damage * 1.2)
            elif attacker.ability() == Ability.GOOEY and current_type == ElementType.POISON:
                base_damage = int(base_damage * 1.2)
            elif attacker.ability() == Ability.REFRIGERATE and current_type == ElementType.ICE:
                base_damage = int(base_damage * 1.2)
            elif attacker.ability() == Ability.PIXILATE and current_type == ElementType.FAIRY:
                base_damage = int(base_damage * 1.2)
            elif attacker.ability() == AttributeError and current_type == ElementType.NORMAL:
                base_damage = int(base_damage * 1.2)

        base_damage = (base_damage // 50) + 2
        base_damage = int(base_damage * random.uniform(0.85, 1.0))
        base_damage = int(base_damage * effectiveness)

        if self.crit_rate == 1:
            if random.randint(0, 15) == 0:
                critical = True
        elif self.crit_rate == 2:
            if random.randint(0, 7) == 0:
                critical = True
        elif self.crit_rate == 3:
            if random.randint(0, 3) == 0:
                critical = True
        elif self.crit_rate >= 4:
            critical = True

        if critical:
            base_damage = int(base_damage * 1.5)
            msg += "A critical hit!\n"

        if attacker.ability() == Ability.RECKLESS and self.damage_class == DamageClass.PHYSICAL:
            base_damage = int(base_damage * 1.2)
        if attacker.ability() == Ability.RECKLESS and self.damage_class == DamageClass.SPECIAL:
            base_damage = int(base_damage * 1.2)

        if self.id != 1108 and self.damage_class != DamageClass.STATUS:
            if attacker.terrain.item != "terrain-extender" and battle.terrain.active():
                pass
            elif battle.terrain.active() and not battle.terrain.item:
                if self.damage_class == DamageClass.PHYSICAL:
                    base_damage = int(base_damage * 0.5)
                if self.damage_class == DamageClass.SPECIAL:
                    base_damage = int(base_damage * 0.5)

        if attacker.nv.burn() and self.damage_class == DamageClass.PHYSICAL and attacker.ability() != Ability.GUTS:
            base_damage = int(base_damage * 0.5)

        if attacker.ability() == Ability.TOXIC_BOOST and self.damage_class == DamageClass.PHYSICAL and attacker.nv.poison():
            base_damage = int(base_damage * 1.5)
        if attacker.ability() == Ability.FLARE_BOOST and self.damage_class == DamageClass.SPECIAL and attacker.nv.burn():
            base_damage = int(base_damage * 1.5)
        if attacker.ability() == Ability.BATTERY and self.damage_class == DamageClass.SPECIAL:
            base_damage = int(base_damage * 1.3)

        if not is_protect_counter:
            if attacker.focus_energy.active():
                if attacker.ability() in (Ability.SNIPER, Ability.MERCiless):
                    if random.randint(0, 2) < 2:
                        critical = True
                else:
                    if random.randint(0, 3) < 1:
                        critical = True

        damage = base_damage

        return damage, critical, is_super_effective, is_not_very_effective

    def apply_damage(self, attacker, defender, battle, damage, current_type, critical, msg):
        """Apply damage to the defender."""
        msg += defender.damage(damage, battle, source=self.pretty_name, critical=critical)

        if not critical and defender.hp > 0 and self.damage_class != DamageClass.STATUS:
            msg += defender.held_item.activate_on_damage(damage_taken=damage, attacker=attacker, move=self, battle=battle)