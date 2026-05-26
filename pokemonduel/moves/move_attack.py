import random
from ..enums import Ability, DamageClass, ElementType


class MoveAttack:
    """Attack calculation and execution."""

    def attack(self, attacker, defender, battle):
        """
        Attacks the defender using this move.
        
        Returns a string of formatted results of this attack and the number of hits this move did.
        """
        #https://bulbapedia.bulbagarden.net/wiki/Damage
        msg = ""
        # pyrefly: ignore [missing-attribute]
        current_type = self.get_type(attacker, defender, battle)
        
        # Move effectiveness
        effectiveness = defender.effectiveness(current_type, battle, attacker=attacker, move=self)
        # pyrefly: ignore [missing-attribute]
        if self.effect == 338:
            effectiveness *= defender.effectiveness(ElementType.FLYING, battle, attacker=attacker, move=self)
        if effectiveness <= 0:
            return ("The attack had no effect!\n", 0) 
        if effectiveness <= .5:
            msg += "It's not very effective...\n"
        elif effectiveness >= 2: 
            msg += "It's super effective!\n"
        
        # Calculate the number of hits for this move.
        parental_bond = False
        # pyrefly: ignore [missing-attribute]
        min_hits = self.min_hits
        # pyrefly: ignore [missing-attribute]
        max_hits = self.max_hits
        if self.effect == 361 and attacker._name == "Greninja-ash":
            hits = 3
        elif min_hits is not None and max_hits is not None:
            # Handle hit range overrides
            if attacker.ability() == Ability.SKILL_LINK:
                min_hits = max_hits
            elif attacker.held_item == "loaded-dice" and max_hits >= 4 and (min_hits < 4 or self.effect == 484):
                min_hits = 4
            # Randomly select number of hits
            if min_hits == 2 and max_hits == 5:
                hits = random.choice([
                    2, 2, 2, 2, 2, 2, 2,
                    3, 3, 3, 3, 3, 3, 3,
                    4, 4, 4,
                    5, 5, 5
                ])
            else:
                hits = random.randint(min_hits, max_hits)
        else:
            if attacker.ability() == Ability.PARENTAL_BOND:
                hits = 2
                parental_bond = True
            else:
                hits = 1
        
        for hit in range(hits):
            if defender.hp == 0:
                break
            # Explosion faints the user first, but should still do damage after death.
            # Future sight still needs to hit after the attacker dies.
            # Mind blown still needs to hit after the attacker dies.
            if attacker.hp == 0 and self.effect not in (8, 149, 420, 444):
                break
            
            # Critical hit chance
            # pyrefly: ignore [missing-attribute]
            critical_stage = self.crit_rate
            if attacker.held_item in ("scope-lens", "razor-claw"):
                critical_stage += 1
            if attacker.ability() == Ability.SUPER_LUCK:
                critical_stage += 1
            if attacker.focus_energy:
                critical_stage += 2
            if attacker.lansat_berry_ate:
                critical_stage += 2
            critical_stage = min(critical_stage, 3)
            crit_map = {
                0: 24,
                1: 8,
                2: 2,
                3: 1,
            }
            critical = not random.randrange(crit_map[critical_stage])
            if attacker.ability() == Ability.MERCILESS and defender.nv.poison():
                critical = True
            # Always scores a critical hit.
            if self.effect == 289:
                critical = True
            if attacker.laser_focus.active():
                critical = True
            if defender.ability(attacker=attacker, move=self) in (Ability.SHELL_ARMOR, Ability.BATTLE_ARMOR):
                critical = False
            if defender.lucky_chant.active():
                critical = False
            # Confusion never crits
            # pyrefly: ignore [missing-attribute]
            if self.id == 0xCFCF:
                critical = False
        
            # Stats
            # pyrefly: ignore [missing-attribute]
            if self.damage_class == DamageClass.PHYSICAL:
                damage_class = DamageClass.PHYSICAL
                a = attacker.get_attack(
                    battle,
                    critical=critical,
                    ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                )
                if self.effect == 304:
                    d = defender.get_raw_defense()
                else:
                    d = defender.get_defense(
                        battle,
                        critical=critical,
                        ignore_stages=attacker.ability() == Ability.UNAWARE,
                        attacker=attacker,
                        move=self
                    )
            else:
                damage_class = DamageClass.SPECIAL
                a = attacker.get_spatk(
                    battle,
                    critical=critical,
                    ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                )
                if self.effect == 304:
                    d = defender.get_raw_spdef()
                else:
                    d = defender.get_spdef(
                        battle,
                        critical=critical,
                        ignore_stages=attacker.ability() == Ability.UNAWARE,
                        attacker=attacker,
                        move=self
                    )
        
            # Always uses defender's defense
            if self.effect == 283:
                d = defender.get_defense(
                    battle,
                    critical=critical,
                    ignore_stages=attacker.ability() == Ability.UNAWARE,
                    attacker=attacker,
                    move=self
                )
            
            # Use the user's defense instead of attack for the attack stat
            if self.effect == 426:
                # This does not pass critical, otherwise it would crop the wrong direction.
                a = attacker.get_defense(
                    battle,
                    ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                )
                
            # Use the defender's attacking stat
            if self.effect == 298:
                if self.damage_class == DamageClass.PHYSICAL:
                    a = defender.get_attack(
                        battle,
                        critical=critical,
                        ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                    )
                else:
                    a = defender.get_spatk(
                        battle,
                        critical=critical,
                        ignore_stages=defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                    )
            
            # Use the higher of attack or special attack
            if self.effect == 416:
                ignore_stages = defender.ability(attacker=attacker, move=self) == Ability.UNAWARE
                a = max(attacker.get_attack(battle, critical=critical, ignore_stages=ignore_stages), attacker.get_spatk(battle, critical=critical, ignore_stages=ignore_stages))
            
            if attacker.flash_fire and current_type == ElementType.FIRE:
                a *= 1.5
            if defender.ability(attacker=attacker, move=self) == Ability.THICK_FAT and current_type in (ElementType.FIRE, ElementType.ICE):
                a *= .5
        
            # pyrefly: ignore [missing-attribute]
            power = self.get_power(attacker, defender, battle)
            if power is None:
                # pyrefly: ignore [missing-attribute]
                raise ValueError(f"{self.name} has no power and no override.")
            
            # Check accuracy on each hit
            # WARNING: If there is something BEFORE this in the loop which adds to msg (like "A critical hit")
            # it MUST be after this block, or it will appear even after "misses" from this move.
            if hit > 0 and not attacker.ability() == Ability.SKILL_LINK:
                # Increasing damage each hit
                if self.effect == 105:
                    # pyrefly: ignore [missing-attribute]
                    if not self.check_hit(attacker, defender, battle):
                        # Reset the number of hits to the number of ACTUAL hits
                        hits = hit
                        break
                    # x2 then x3
                    power *= 1 + hit
                # Only checks if loaded dice did not activate
                if self.effect == 484 and attacker.held_item != "loaded-dice":
                    # pyrefly: ignore [missing-attribute]
                    if not self.check_hit(attacker, defender, battle):
                        hits = hit
                        break
            
            # --- Showdown-accurate damage formula ---
            # Step 1: Base damage with integer flooring at each step
            # floor(floor(floor(2*L/5+2) * Bp * A/D) / 50 + 2)
            damage = int(int(int(2 * attacker.level / 5) + 2) * power * a / d)
            damage = int(damage / 50) + 2

            # Step 2: Critical hit (1.5x, floored)
            if critical:
                msg += "A critical hit!\n"
                damage = int(damage * 3 / 2)

            # Step 3: Weather type boosts (before random, matches Showdown ordering)
            # Harsh sun/rain (h-sun/h-rain) give the same boost as normal sun/rain
            weather = battle.weather.get()
            if current_type == ElementType.WATER and weather in ("rain", "h-rain"):
                damage = int(damage * 3 / 2)
            elif current_type == ElementType.FIRE and weather in ("rain", "h-rain"):
                damage = int(damage / 2)
            elif current_type == ElementType.FIRE and weather in ("sun", "h-sun"):
                damage = int(damage * 3 / 2)
            elif current_type == ElementType.WATER and weather in ("sun", "h-sun"):
                damage = int(damage / 2)

            # Step 4: Random damage roll (Showdown integer method: 85-100, floor)
            damage = damage * random.randint(85, 100) // 100
            
        
            # Same type attack bonus - extra damage for using a move that is the same type as your poke's type.
            if current_type in attacker.type_ids:
                if attacker.ability() == Ability.ADAPTABILITY:
                    damage *= 2
                else:
                    damage *= 1.5
        
            # Move effectiveness
            damage *= effectiveness
        
            # Burn
            if (
                attacker.nv.burn()
                and damage_class == DamageClass.PHYSICAL
                and attacker.ability() != Ability.GUTS
                and self.effect != 170
            ):
                damage *= .5
        
            # Aurora Veil, Light Screen, Reflect do not stack but all reduce incoming damage in some way
            if not critical and attacker.ability() != Ability.INFILTRATOR:
                if defender.owner.aurora_veil.active():
                    damage *= .5
                elif defender.owner.light_screen.active() and damage_class == DamageClass.SPECIAL:
                    damage *= .5
                elif defender.owner.reflect.active() and damage_class == DamageClass.PHYSICAL:
                    damage *= .5
        
            # Moves that do extra damage to minimized pokes
            if defender.minimized and self.effect == 338:
                damage *= 2
            
            # Fluffy
            if defender.ability(attacker=attacker, move=self) == Ability.FLUFFY:
                # pyrefly: ignore [missing-attribute]
                if self.makes_contact(attacker):
                    damage *= .5
                if current_type == ElementType.FIRE:
                    damage *= 2
        
            # Abilities that change damage
            if defender.ability(attacker=attacker, move=self) in (Ability.FILTER, Ability.PRISM_ARMOR, Ability.SOLID_ROCK) and effectiveness > 1:
                damage *= .75
            if attacker.ability() == Ability.NEUROFORCE and effectiveness > 1:
                damage *= 1.25
            if defender.ability(attacker=attacker, move=self) == Ability.ICE_SCALES and damage_class == DamageClass.SPECIAL:
                damage *= .5
            if attacker.ability() == Ability.SNIPER and critical:
                damage *= 1.5
            if attacker.ability() == Ability.TINTED_LENS and effectiveness < 1:
                damage *= 2
            # pyrefly: ignore [missing-attribute]
            if attacker.ability() == Ability.PUNK_ROCK and self.is_sound_based():
                damage *= 1.3
            # pyrefly: ignore [missing-attribute]
            if defender.ability(attacker=attacker, move=self) == Ability.PUNK_ROCK and self.is_sound_based():
                damage *= .5
            if defender.ability(attacker=attacker, move=self) == Ability.HEATPROOF and current_type == ElementType.FIRE:
                damage *= .5
            if defender.ability(attacker=attacker, move=self) == Ability.PURIFYING_SALT and current_type == ElementType.GHOST:
                damage *= .5
            if Ability.DARK_AURA in (attacker.ability(), defender.ability(attacker=attacker, move=self)) and current_type == ElementType.DARK:
                if Ability.AURA_BREAK in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
                    damage *= .75
                else:
                    damage *= 4/3
            if Ability.FAIRY_AURA in (attacker.ability(), defender.ability(attacker=attacker, move=self)) and current_type == ElementType.FAIRY:
                if Ability.AURA_BREAK in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
                    damage *= .75
                else:
                    damage *= 4/3
            if defender.ability(attacker=attacker, move=self) == Ability.DRY_SKIN and current_type == ElementType.FIRE:
                damage *= 1.25
        
            # Items that change damage
            if defender.held_item == "chilan-berry" and current_type == ElementType.NORMAL:
                damage *= .5
            if attacker.held_item == "expert-belt" and effectiveness > 1:
                damage *= 1.2
            if (
                attacker.held_item == "life-orb"
                and self.damage_class != DamageClass.STATUS
                and self.effect != 149
            ):
                damage *= 1.3
            if attacker.held_item == "metronome":
                # pyrefly: ignore [missing-attribute]
                damage *= attacker.metronome.get_buff(self.name)
            
            # Parental bond - adds an extra low power hit
            if parental_bond and hit > 0:
                damage *= .25
            
            # Reduced damage while at full hp
            if defender.ability(attacker=attacker, move=self) in (Ability.MULTISCALE, Ability.SHADOW_SHIELD) and defender.hp == defender.starting_hp:
                damage *= .5

            # Random damage scaling
            damage *= random.uniform(0.85, 1)
            damage = max(1, int(damage))
            
            # Cannot lower the target's HP below 1.
            if self.effect == 102:
                damage = min(damage, defender.hp - 1)
            
            # Drain ratios
            drain_heal_ratio = None
            if self.effect in (4, 9, 346, 500):
                drain_heal_ratio = 1/2
            elif self.effect == 349:
                drain_heal_ratio = 3/4

            # Do the damage
            msgadd, damage = defender._damage(damage, battle, move=self, move_type=current_type, attacker=attacker, critical=critical, drain_heal_ratio=drain_heal_ratio)
            msg += msgadd
            
            # Recoil
            if attacker.ability() != Ability.ROCK_HEAD and defender.owner.has_alive_pokemon():
                if self.effect == 49:
                    msg += attacker.damage(damage // 4, battle, source="recoil")
                if self.effect in (199, 254, 263, 469):
                    msg += attacker.damage(damage // 3, battle, source="recoil")
                if self.effect == 270:
                    msg += attacker.damage(damage // 2, battle, source="recoil")
                if self.effect == 463:
                    msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
        
        # Weakness Policy
        if effectiveness > 1 and defender.held_item == "weakness-policy" and not defender.substitute:
            msg += defender.append_attack(2, attacker=defender, move=self, source="its weakness policy")
            msg += defender.append_spatk(2, attacker=defender, move=self, source="its weakness policy")
            # pyrefly: ignore [missing-attribute]
            defender.held_item.use()
        
        return (msg, hits)

    def calculate_damage(self, attacker, defender, battle, current_type, effectiveness, is_protect_counter):
        """Calculate damage dealt by the move."""
        # pyrefly: ignore [missing-attribute]
        power = self.get_power(attacker, defender, battle)
        if power == 0:
            return 0, False, False, False

        from ..enums import MoveTarget

        is_super_effective = effectiveness >= 2
        is_not_very_effective = effectiveness <= 0.5
        critical = False

        level = attacker.level
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.DEBUG:
            level = 100

        # pyrefly: ignore [missing-attribute]
        if self.id == 573 and attacker.ability() == Ability.ORDINARY:
            level *= 2

        attack_stat = attacker.get_attack()
        defense_stat = defender.get_defense()

        # pyrefly: ignore [missing-attribute]
        if self.damage_class == DamageClass.SPECIAL:
            attack_stat = attacker.get_spatk()
            defense_stat = defender.get_spdef()

        # pyrefly: ignore [missing-attribute]
        if self.effect == 222:
            if self.damage_class == DamageClass.PHYSICAL:
                attack_stat = attacker.get_spatk()
            else:
                defense_stat = defender.get_defense()

        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.UNIBLOW:
            attack_stat *= 1.5
        # pyrefly: ignore [missing-attribute]
        if defender.ability() == Ability.UNIBLOW:
            defense_stat *= 1.5

        if attacker.terrain.item == "terrain-extender" and battle.terrain.item:
            pass
        # pyrefly: ignore [missing-attribute]
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

            # pyrefly: ignore [missing-attribute]
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

        # pyrefly: ignore [missing-attribute]
        if self.crit_rate == 1:
            if random.randint(0, 15) == 0:
                critical = True
        elif self.crit_rate == 2:
            if random.randint(0, 7) == 0:
                critical = True
        elif self.crit_rate == 3:
            if random.randint(0, 3) == 0:
                critical = True
        # pyrefly: ignore [unsupported-operation]
        elif self.crit_rate >= 4:
            critical = True

        if critical:
            base_damage = int(base_damage * 1.5)
            # pyrefly: ignore [unbound-name]
            msg += "A critical hit!\n"

        if attacker.ability() == Ability.RECKLESS and self.damage_class == DamageClass.PHYSICAL:
            base_damage = int(base_damage * 1.2)
        if attacker.ability() == Ability.RECKLESS and self.damage_class == DamageClass.SPECIAL:
            base_damage = int(base_damage * 1.2)

        # pyrefly: ignore [missing-attribute]
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
                # pyrefly: ignore [missing-attribute]
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
        # pyrefly: ignore [missing-attribute]
        msg += defender.damage(damage, battle, source=self.pretty_name, critical=critical)

        # pyrefly: ignore [missing-attribute]
        if not critical and defender.hp > 0 and self.damage_class != DamageClass.STATUS:
            msg += defender.held_item.activate_on_damage(damage_taken=damage, attacker=attacker, move=self, battle=battle)
