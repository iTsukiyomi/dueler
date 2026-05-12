import random
from ..enums import Ability, DamageClass, MoveTarget, ElementType

class MoveChecks:
    """Move validation and checking methods."""

    def check_executable(self, attacker, defender, battle):
        """
        Returns True if the move can be executed, False otherwise
        
        Checks different requirements for moves that can make them fail.
        """
        if attacker.taunt.active() and self.damage_class == DamageClass.STATUS:
            return False
        if attacker.silenced.active() and self.is_sound_based():
            return False
        if self.is_affected_by_heal_block() and attacker.heal_block.active():
            return False
        if self.is_powder_or_spore() and (ElementType.GRASS in defender.type_ids or defender.ability(attacker=attacker, move=self) == Ability.OVERCOAT or defender.held_item == "safety-goggles"):
            return False
        if battle.weather.get() == "h-sun" and self.get_type(attacker, defender, battle) == ElementType.WATER and self.damage_class != DamageClass.STATUS:
            return False
        if battle.weather.get() == "h-rain" and self.get_type(attacker, defender, battle) == ElementType.FIRE and self.damage_class != DamageClass.STATUS:
            return False
        if attacker.disable.active() and attacker.disable.item is self:
            return False
        if attacker is not defender and defender.imprison and self.id in [x.id for x in defender.moves]:
            return False
        #Since we only have single battles, these moves always fail
        if self.effect in (173, 301, 308, 316, 363, 445, 494):
            return False
        if self.effect in (93, 98) and not attacker.nv.sleep():
            return False
        if self.effect in (9, 108) and not defender.nv.sleep():
            return False
        if self.effect == 364 and not defender.nv.poison():
            return False
        if self.effect in (162, 163) and attacker.stockpile == 0:
            return False
        if self.effect == 85 and (ElementType.GRASS in defender.type_ids or defender.leech_seed):
            return False
        if self.effect == 193 and attacker.imprison:
            return False
        if self.effect == 166 and defender.torment:
            return False
        if self.effect == 91 and (defender.encore.active() or defender.last_move is None or defender.last_move.pp == 0):
            return False
        if self.effect == 87 and (defender.disable.active() or defender.last_move is None or defender.last_move.pp == 0):
            return False
        if self.effect in (96, 101) and (defender.last_move is None or defender.last_move.pp == 0):
            return False
        if self.effect == 176 and defender.taunt.active():
            return False
        if self.effect == 29 and not defender.owner.valid_swaps(attacker, battle, check_trap=False):
            return False
        if self.effect in (128, 154, 493) and not attacker.owner.valid_swaps(defender, battle, check_trap=False):
            return False
        if self.effect == 161 and attacker.stockpile >= 3:
            return False
        if self.effect in (90, 145, 228, 408) and attacker.last_move_damage is None:
            return False
        if self.effect == 145 and attacker.last_move_damage[1] != DamageClass.SPECIAL:
            return False
        if self.effect in (90, 408) and attacker.last_move_damage[1] != DamageClass.PHYSICAL:
            return False
        if self.effect in (10, 243) and (defender.last_move is None or not defender.last_move.selectable_by_mirror_move()):
            return False
        if self.effect == 83 and (defender.last_move is None or not defender.last_move.selectable_by_mimic()):
            return False
        if self.effect == 180 and attacker.owner.wish.active():
            return False
        if self.effect == 388 and defender.attack_stage == -6:
            return False
        if self.effect in (143, 485, 493) and attacker.hp <= attacker.starting_hp // 2:
            return False
        if self.effect == 414 and attacker.hp < attacker.starting_hp // 3:
            return False
        if self.effect == 80 and attacker.hp <= attacker.starting_hp // 4:
            return False
        if self.effect == 48 and attacker.focus_energy:
            return False
        if self.effect == 190 and attacker.hp >= defender.hp:
            return False
        if self.effect == 194 and not (attacker.nv.burn() or attacker.nv.paralysis() or attacker.nv.poison()):
            return False
        if self.effect == 235 and (not attacker.nv.current or defender.nv.current):
            return False
        if self.effect in (121, 266) and ("-x" in (attacker.gender, defender.gender) or attacker.gender == defender.gender or defender.ability(attacker=attacker, move=self) == Ability.OBLIVIOUS):
            return False
        if self.effect in (367, 392) and attacker.ability() not in (Ability.PLUS, Ability.MINUS):
            return False
        if self.effect == 39 and attacker.level < defender.level:
            return False
        if self.effect in (46, 86, 156, 264, 286) and battle.gravity.active():
            return False
        if self.effect == 113 and defender.owner.spikes == 3:
            return False
        if self.effect == 250 and defender.owner.toxic_spikes == 2:
            return False
        if self.effect in (159, 377, 383) and attacker.active_turns != 0:
            return False
        if self.effect == 98 and not any(m.selectable_by_sleep_talk() for m in attacker.moves):
            return False
        if self.effect == 407 and not battle.weather.get() == "hail":
            return False
        if self.effect == 407 and attacker.owner.aurora_veil.active():
            return False
        if self.effect == 47 and attacker.owner.mist.active():
            return False
        if self.effect in (80, 493) and attacker.substitute:
            return False
        if self.effect == 398 and ElementType.FIRE not in attacker.type_ids:
            return False
        if self.effect == 481 and ElementType.ELECTRIC not in attacker.type_ids:
            return False
        if self.effect == 376 and ElementType.GRASS in defender.type_ids:
            return False
        if self.effect == 343 and ElementType.GHOST in defender.type_ids:
            return False
        if self.effect == 107 and defender.trapping:
            return False
        if self.effect == 182 and attacker.ingrain:
            return False
        if self.effect == 94 and self.get_conversion_2(attacker, defender, battle) is None:
            return False
        if self.effect == 121 and defender.infatuated is attacker:
            return False
        if self.effect == 248 and defender.ability(attacker=attacker, move=self) == Ability.INSOMNIA:
            return False
        if self.effect in (242, 249) and (defender.has_moved or isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.damage_class == DamageClass.STATUS):
            return False
        if self.effect == 252 and attacker.aqua_ring:
            return False
        if self.effect == 253 and attacker.magnet_rise.active():
            return False
        if self.effect == 221 and attacker.owner.healing_wish:
            return False
        if self.effect == 271 and attacker.owner.lunar_dance:
            return False
        if self.effect in (240, 248, 299, 300) and not defender.ability_changeable():
            return False
        if self.effect == 300 and not attacker.ability_giveable():
            return False
        if self.effect == 241 and attacker.lucky_chant.active():
            return False
        if self.effect == 125 and attacker.owner.safeguard.active():
            return False
        if self.effect == 293 and not set(attacker.type_ids) & set(defender.type_ids):
            return False
        if self.effect == 295 and defender.ability(attacker=attacker, move=self) == Ability.MULTITYPE:
            return False
        if self.effect == 319 and not defender.type_ids:
            return False
        if self.effect == 171 and attacker.last_move_damage is not None:
            return False
        if self.effect == 179 and not (attacker.ability_changeable() and defender.ability_giveable()):
            return False
        if self.effect == 181 and attacker.get_assist_move() is None:
            return False
        if self.effect in (112, 117, 184, 195, 196, 279, 307, 345, 350, 354, 356, 362, 378, 384, 454, 488, 499) and defender.has_moved:
            return False
        if self.effect == 192 and not (attacker.ability_changeable() and attacker.ability_giveable() and defender.ability_changeable() and defender.ability_giveable()):
            return False
        if self.effect == 226 and attacker.owner.tailwind.active():
            return False
        if self.effect in (90, 92, 145) and attacker.substitute:
            return False
        if self.effect in (85, 92, 169, 178, 188, 206, 388) and defender.substitute:
            return False
        if self.effect == 234 and (not attacker.held_item.power or attacker.ability() == Ability.STICKY_HOLD):
            return False
        if self.effect == 178 and (Ability.STICKY_HOLD in (attacker.ability(), defender.ability(attacker=attacker, move=self)) or not attacker.held_item.can_remove() or not defender.held_item.can_remove()):
            return False
        if self.effect == 202 and attacker.owner.mud_sport.active():
            return False
        if self.effect == 211 and attacker.owner.water_sport.active():
            return False
        if self.effect == 149 and defender.owner.future_sight.active():
            return False
        if self.effect == 188 and (defender.nv.current or defender.ability(attacker=attacker, move=self) in (Ability.INSOMNIA, Ability.VITAL_SPIRIT, Ability.SWEET_VEIL) or defender.yawn.active()):
            return False
        if self.effect == 188 and battle.terrain.item == "electric" and attacker.grounded(battle):
            return False
        if self.effect in (340, 351) and not any(ElementType.GRASS in p.type_ids and p.grounded(battle) and not p.dive and not p.dig and not p.fly and not p.shadow_force for p in (attacker, defender)):
            return False
        if self.effect == 341 and defender.owner.sticky_web:
            return False
        if self.effect in (112, 117, 356, 362, 384, 454, 488, 499) and random.randint(1, attacker.protection_chance) != 1:
            return False
        if self.effect == 403 and (defender.last_move is None or defender.last_move.pp == 0 or not defender.last_move.selectable_by_instruct() or defender.locked_move is not None):
            return False
        if self.effect == 378 and (ElementType.GRASS in defender.type_ids or defender.ability(attacker=attacker, move=self) == Ability.OVERCOAT or defender.held_item == "safety-goggles"):
            return False
        if self.effect == 233 and defender.embargo.active():
            return False
        if self.effect == 324 and (not attacker.held_item.has_item() or defender.held_item.has_item() or not attacker.held_item.can_remove()):
            return False
        if self.effect == 185 and (attacker.held_item.has_item() or attacker.held_item.last_used is None):
            return False
        if self.effect == 430 and (not defender.held_item.has_item() or not defender.held_item.can_remove() or defender.corrosive_gas):
            return False
        if self.effect == 114 and defender.foresight:
            return False
        if self.effect == 217 and defender.miracle_eye:
            return False
        if self.effect == 38 and (attacker.nv.sleep() or attacker.hp == attacker.starting_hp or attacker._name == "Minior"):
            return False
        if self.effect == 427 and attacker.no_retreat:
            return False
        if self.effect == 99 and attacker.destiny_bond_cooldown.active():
            return False
        if self.effect in (116, 137, 138, 165) and battle.weather.get() in ("h-rain", "h-sun", "h-wind"):
            return False
        if self.effect in (8, 420, 444) and Ability.DAMP in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
            return False
        if self.effect in (223, 453) and not attacker.held_item.is_berry():
            return False
        if self.effect == 369 and battle.terrain.item == "electric":
            return False
        if self.effect == 352 and battle.terrain.item == "grassy":
            return False
        if self.effect == 353 and battle.terrain.item == "misty":
            return False
        if self.effect == 395 and battle.terrain.item == "psychic":
            return False
        if self.effect == 66 and attacker.owner.reflect.active():
            return False
        if self.effect == 36 and attacker.owner.light_screen.active():
            return False
        if self.effect == 110 and ElementType.GHOST in attacker.type_ids and defender.cursed:
            return False
        if self.effect == 58 and (defender.substitute or defender.illusion_name is not None):
            return False
        if self.effect == 446 and defender.held_item.get() is None:
            return False
        if self.effect == 448 and not battle.terrain.item:
            return False
        if self.effect == 452 and defender.octolock:
            return False
        if self.effect == 280 and any([defender.defense_split, defender.spdef_split, attacker.defense_split, attacker.spdef_split]):
            return False
        if self.effect == 281 and any([defender.attack_split, defender.spatk_split, attacker.attack_split, attacker.spatk_split]):
            return False
        if self.effect == 456 and (defender.type_ids == [ElementType.PSYCHIC] or defender.ability(attacker=attacker, move=self) == Ability.RKS_SYSTEM):
            return False
        if self.effect == 83 and self not in attacker.moves:
            return False
        if self.effect == 501 and (defender.has_moved or isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.get_priority(defender, attacker, battle) <= 0):
            return False
        if defender.ability(attacker=attacker, move=self) in (Ability.QUEENLY_MAJESTY, Ability.DAZZLING, Ability.ARMOR_TAIL) and self.get_priority(attacker, defender, battle) > 0:
            return False
        return True
    
    def check_semi_invulnerable(self, attacker, defender, battle):
        """
        Returns True if this move hits, False otherwise.
        
        Checks if a pokemon is in the semi-invulnerable turn of dive or dig.
        """
        if not self.targets_opponent():
            return True
        if Ability.NO_GUARD in (attacker.ability(), defender.ability(attacker=attacker, move=self)):
            return True
        if defender.mind_reader.active() and defender.mind_reader.item is attacker:
            return True
        if defender.dive and self.effect not in (258, 262):
            return False
        if defender.dig and self.effect not in (127, 148):
            return False
        if defender.fly and self.effect not in (147, 150, 153, 208, 288, 334, 373):
            return False
        if defender.shadow_force:
            return False
        return True
    
    def check_protect(self, attacker, defender, battle):
        """
        Returns True if this move hits, False otherwise.
        
        Checks if this pokemon is protected by a move like protect or wide guard.
        Also returns a formatted message.
        """
        msg = ""
        # Moves that don't target the opponent can't be protected by the target.
        if not self.targets_opponent():
            return True, msg
        # Moves which bypass all protection.
        if self.effect in (149, 224, 273, 360, 438, 489):
            return True, msg
        if attacker.ability() == Ability.UNSEEN_FIST and self.makes_contact(attacker):
            return True, msg
        if defender.crafty_shield and self.damage_class == DamageClass.STATUS:
            return False, msg
        # Moves which bypass all protection except for crafty shield.
        if self.effect in (29, 107, 179, 412):
            return True, msg
        if defender.protect:
            return False, msg
        if defender.spiky_shield:
            if self.makes_contact(attacker) and attacker.held_item != "protective-pads":
                msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{defender.name}'s spiky shield")
            return False, msg
        if defender.baneful_bunker:
            if self.makes_contact(attacker) and attacker.held_item != "protective-pads":
                msg += attacker.nv.apply_status("poison", battle, attacker=defender, source=f"{defender.name}'s baneful bunker")
            return False, msg
        if defender.wide_guard and self.targets_multiple():
            return False, msg
        if self.get_priority(attacker, defender, battle) > 0 and battle.terrain.item == "psychic" and defender.grounded(battle, attacker=attacker, move=self):
            return False, msg
        if defender.mat_block and self.damage_class != DamageClass.STATUS:
            return False, msg
        if defender.king_shield and self.damage_class != DamageClass.STATUS:
            if self.makes_contact(attacker) and attacker.held_item != "protective-pads":
                msg += attacker.append_attack(-1, attacker=defender, move=self, source=f"{defender.name}'s silk trap")
            return False, msg
        if defender.obstruct and self.damage_class != DamageClass.STATUS:
            if self.makes_contact(attacker) and attacker.held_item != "protective-pads":
                msg += attacker.append_defense(-2, attacker=defender, move=self, source=f"{defender.name}'s silk trap")
            return False, msg
        if defender.silk_trap and self.damage_class != DamageClass.STATUS:
            if self.makes_contact(attacker) and attacker.held_item != "protective-pads":
                msg += attacker.append_speed(-1, attacker=defender, move=self, source=f"{defender.name}'s silk trap")
            return False, msg
        if defender.burning_bulwark and self.damage_class != DamageClass.STATUS:
            if self.makes_contact(attacker) and attacker.held_item != "protective-pads":
                msg += attacker.nv.apply_status("burn", battle, attacker=defender, source=f"{defender.name}'s burning bulwark")
            return False, msg
        if defender.quick_guard and self.get_priority(attacker, defender, battle) > 0:
            return False, msg
        return True, msg
    
    def check_hit(self, attacker, defender, battle):
        """
        Returns True if this move hits, False otherwise.
        
        Calculates the chance to hit & does an RNG check using that chance.
        """
        micle_used = attacker.micle_berry_ate
        attacker.micle_berry_ate = False
        #Moves that have a None accuracy always hit.
        if self.accuracy is None:
            return True
        
        # During hail, this bypasses accuracy checks
        if self.effect == 261 and battle.weather.get() == "hail":
            return True
        # During rain, this bypasses accuracy checks
        if self.effect in (153, 334, 357, 365, 396) and battle.weather.get() in ("rain", "h-rain"):
            return True
        # If used by a poison type, this bypasses accuracy checks
        if self.effect == 34 and ElementType.POISON in attacker.type_ids:
            return True
        # If used against a minimized poke, this bypasses accuracy checks
        if self.effect == 338 and defender.minimized:
            return True
        
        # These DO allow OHKO moves to bypass accuracy checks
        if self.targets_opponent():
            if defender.mind_reader.active() and defender.mind_reader.item is attacker:
                return True
            if attacker.ability() == Ability.NO_GUARD:
                return True
            if defender.ability(attacker=attacker, move=self) == Ability.NO_GUARD:
                return True
        
        # OHKO moves
        if self.effect == 39:
            accuracy = 30 + (attacker.level - defender.level)
            return random.uniform(0, 100) <= accuracy
        
        # This does NOT allow OHKO moves to bypass accuracy checks
        if attacker.telekinesis.active():
            return True
            
        
        accuracy = self.accuracy
        # When used during harsh sunlight, this has an accuracy of 50%
        if self.effect in (153, 334) and battle.weather.get() in ("sun", "h-sun"):
            accuracy = 50
        if self.targets_opponent():
            if defender.ability(attacker=attacker, move=self) == Ability.WONDER_SKIN and self.damage_class == DamageClass.STATUS:
                accuracy = 50
        
        if defender.ability(attacker=attacker, move=self) == Ability.UNAWARE:
            stage = 0
        else:
            stage = attacker.get_accuracy(battle)
        if not (
            self.effect == 304
            or defender.foresight
            or defender.miracle_eye
            or attacker.ability() in [Ability.UNAWARE, Ability.KEEN_EYE, Ability.MINDS_EYE]
        ):
            stage -= defender.get_evasion(battle)
        stage = min(6, max(-6, stage))
        stage_multiplier = {
            -6: 3/9,
            -5: 3/8,
            -4: 3/7,
            -3: 3/6,
            -2: 3/5,
            -1: 3/4,
            0: 1,
            1: 4/3,
            2: 5/3,
            3: 2,
            4: 7/3,
            5: 8/3,
            6: 3,
        }
        accuracy *= stage_multiplier[stage]
        if self.targets_opponent():
            if defender.ability(attacker=attacker, move=self) == Ability.TANGLED_FEET and defender.confusion.active():
                accuracy *= .5
            if defender.ability(attacker=attacker, move=self) == Ability.SAND_VEIL and battle.weather.get() == "sandstorm":
                accuracy *= .8
            if defender.ability(attacker=attacker, move=self) == Ability.SNOW_CLOAK and battle.weather.get() == "hail":
                accuracy *= .8
        if attacker.ability() == Ability.COMPOUND_EYES:
            accuracy *= 1.3
        if attacker.ability() == Ability.HUSTLE and self.damage_class == DamageClass.PHYSICAL:
            accuracy *= .8
        if attacker.ability() == Ability.VICTORY_STAR:
            accuracy *= 1.1
        if battle.gravity.active():
            accuracy *= (5 / 3)
        if attacker.held_item == "wide-lens":
            accuracy *= 1.1
        if attacker.held_item == "zoom-lens" and defender.has_moved:
            accuracy *= 1.2
        if defender.held_item == "bright-powder":
            accuracy *= .9
        if micle_used:
            accuracy *= 1.2

        return random.uniform(0, 100) <= accuracy
    
    def check_effective(self, attacker, defender, battle):
        """
        Returns True if a move has an effect on a poke.
        
        Moves can have no effect based on things like type effectiveness and groundedness.
        """
        # What if I :flushed: used Hold Hands :flushed: in a double battle :flushed: with you? :flushed:
        # (and you weren't protected by Crafty Shield or in the semi-invulnerable turn of a move like Fly or Dig)
        if self.effect in (86, 174, 368, 370, 371, 389):
            return False
        
        if not self.targets_opponent():
            return True
        
        if self.effect == 266 and defender.ability(attacker=attacker, move=self) == Ability.OBLIVIOUS:
            return False
        if self.effect == 39 and defender.ability(attacker=attacker, move=self) == Ability.STURDY:
            return False
        if self.effect == 39 and self.id == 329 and ElementType.ICE in defender.type_ids:
            return False
        if self.effect == 400 and not defender.nv.current:
            return False
        if self.is_sound_based() and defender.ability(attacker=attacker, move=self) == Ability.SOUNDPROOF:
            return False
        if self.is_ball_or_bomb() and defender.ability(attacker=attacker, move=self) == Ability.BULLETPROOF:
            return False
        if attacker.ability() == Ability.PRANKSTER and ElementType.DARK in defender.type_ids:
            if self.damage_class == DamageClass.STATUS:
                return False
            # If the attacker used a status move that called this move, even if this move is not a status move then it should still be considered affected by prankster.
            if not isinstance(attacker.owner.selected_action, int) and attacker.owner.selected_action.damage_class == DamageClass.STATUS:
                return False
        if defender.ability(attacker=attacker, move=self) == Ability.GOOD_AS_GOLD and self.damage_class == DamageClass.STATUS:
            return False
        
        # Status moves do not care about type effectiveness - except for thunder wave FOR SOME REASON...
        if self.damage_class == DamageClass.STATUS and self.id != 86:
            return True
        
        current_type = self.get_type(attacker, defender, battle)
        if current_type == ElementType.TYPELESS:
            return True
        effectiveness = defender.effectiveness(current_type, battle, attacker=attacker, move=self)
        if self.effect == 338:
            effectiveness *= defender.effectiveness(ElementType.FLYING, battle, attacker=attacker, move=self)
        if effectiveness == 0:
            return False
        
        if current_type == ElementType.GROUND and not defender.grounded(battle, attacker=attacker, move=self) and self.effect != 373 and not battle.inverse_battle:
            return False
        if self.effect != 459:
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.VOLT_ABSORB and defender.hp == defender.starting_hp:
                return False
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) in (Ability.WATER_ABSORB, Ability.DRY_SKIN) and defender.hp == defender.starting_hp:
                return False
        if current_type == ElementType.FIRE and defender.ability(attacker=attacker, move=self) == Ability.FLASH_FIRE and defender.flash_fire:
            return False
        if effectiveness <= 1 and defender.ability(attacker=attacker, move=self) == Ability.WONDER_GUARD:
            return False
        
        return True


class MoveHelpers:
    """Helper methods for move properties."""

    def is_sound_based(self):
        """Whether or not this move is sound based."""
        return self.id in [
            45, 46, 47, 48, 103, 173, 195, 215, 253, 304, 319, 320, 336, 405, 448, 496, 497, 547,
            555, 568, 574, 575, 586, 590, 664, 691, 728, 744, 753, 826, 871, 1005, 1006
        ]
    
    def is_punching(self):
        """Whether or not this move is a punching move."""
        return self.id in [
            4, 5, 7, 8, 9, 146, 183, 223, 264, 309, 325, 327, 359, 409, 418, 612, 665, 721, 729,
            764, 765, 834, 857, 889
        ]
    
    def is_biting(self):
        """Whether or not this move is a biting move."""
        return self.id in [44, 158, 242, 305, 422, 423, 424, 706, 733, 742]
    
    def is_ball_or_bomb(self):
        """Whether or not this move is a ball or bomb move."""
        return self.id in [
            121, 140, 188, 190, 192, 247, 296, 301, 311, 331, 350, 360, 396, 402, 411, 412, 426,
            439, 443, 486, 491, 545, 676, 690, 748, 1017
        ]
    
    def is_aura_or_pulse(self):
        """Whether or not this move is an aura or pulse move."""
        return self.id in [352, 396, 399, 406, 505, 618, 805]
    
    def is_powder_or_spore(self):
        """Whether or not this move is a powder or spore move."""
        return self.id in [77, 78, 79, 147, 178, 476, 600, 737]
    
    def is_dance(self):
        """Whether or not this move is a dance move."""
        return self.id in [14, 80, 297, 298, 349, 461, 483, 552, 686, 744, 846, 872]
    
    def is_slicing(self):
        """Whether or not this move is a slicing move."""
        return self.id in [
            15, 75, 163, 210, 314, 332, 348, 400, 403, 404, 427, 440, 533, 534, 669, 749, 830, 845,
            860, 869, 891, 895, 1013, 1014
        ]
    
    def is_wind(self):
        """Whether or not this move is a wind move."""
        return self.id in [16, 18, 59, 196, 201, 239, 257, 314, 366, 542, 572, 584, 829, 842, 844, 849]
    
    def is_affected_by_magic_coat(self):
        """Whether or not this move can be reflected by magic coat and magic bounce."""
        return self.id in [
            18, 28, 39, 43, 45, 46, 47, 48, 50, 73, 77, 78, 79, 81, 86, 92, 95, 103, 108, 109, 134,
            137, 139, 142, 147, 148, 169, 178, 180, 184, 186, 191, 193, 204, 207, 212, 213, 227, 230,
            259, 260, 261, 269, 281, 297, 313, 316, 319, 320, 321, 335, 357, 373, 377, 380, 388, 390,
            432, 445, 446, 464, 477, 487, 493, 494, 505, 564, 567, 568, 571, 575, 576, 589, 590, 598,
            599, 600, 608, 666, 668, 671, 672, 685, 715, 736, 737, 810
        ]
    
    def is_affected_by_heal_block(self):
        """Whether or not this move cannot be selected during heal block."""
        return self.id in [
            71, 72, 105, 135, 138, 141, 156, 202, 208, 234, 235, 236, 256, 273, 303, 355, 361, 409,
            456, 461, 505, 532, 570, 577, 613, 659, 666, 668, 685
        ]
    
    def is_affected_by_substitute(self):
        """Whether or not this move is able to bypass a substitute."""
        return self.id not in [
            18, 45, 46, 47, 48, 50, 102, 103, 114, 166, 173, 174, 176, 180, 193, 195, 213, 215, 227,
            244, 253, 259, 269, 270, 272, 285, 286, 304, 312, 316, 319, 320, 357, 367, 382, 384, 385,
            391, 405, 448, 495, 496, 497, 513, 516, 547, 555, 568, 574, 575, 586, 587, 589, 590, 593,
            597, 600, 602, 607, 621, 664, 674, 683, 689, 691, 712, 728, 753, 826, 871, 1005, 1006
        ]
    
    def targets_opponent(self):
        """Whether or not this move targets the opponent."""
        #Moves which don't follow normal targeting protocals, ignore them unless they are damaging.
        if self.target == MoveTarget.SPECIFIC_MOVE and self.damage_class == DamageClass.STATUS:
            return False
        #Moves which do not target the opponent pokemon.
        return self.target not in (
            MoveTarget.SELECTED_POKEMON_ME_FIRST,
            MoveTarget.ALLY,
            MoveTarget.USERS_FIELD,
            MoveTarget.USER_OR_ALLY,
            MoveTarget.OPPONENTS_FIELD,
            MoveTarget.USER,
            MoveTarget.ENTIRE_FIELD,
            MoveTarget.USER_AND_ALLIES,
            MoveTarget.ALL_ALLIES,
        )
    
    def targets_multiple(self):
        """Whether or not this move targets multiple pokemon."""
        return self.target in (
            MoveTarget.ALL_OTHER_POKEMON,
            MoveTarget.ALL_OPPONENTS,
            MoveTarget.USER_AND_ALLIES,
            MoveTarget.ALL_POKEMON,
            MoveTarget.ALL_ALLIES,
        )
    
    def makes_contact(self, attacker):
        """Whether or not this move makes contact."""
        return self.id in [
            1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 15, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 29,
            30, 31, 32, 33, 34, 35, 36, 37, 38, 44, 64, 65, 66, 67, 68, 69, 70, 80, 91, 98, 99,
            117, 122, 127, 128, 130, 132, 136, 141, 146, 152, 154, 158, 162, 163, 165, 167, 168,
            172, 175, 179, 183, 185, 200, 205, 206, 209, 210, 211, 216, 218, 223, 224, 228, 229,
            231, 232, 233, 238, 242, 245, 249, 252, 263, 264, 265, 276, 279, 280, 282, 283, 291,
            292, 299, 301, 302, 305, 306, 309, 310, 325, 327, 332, 337, 340, 342, 343, 344, 348,
            358, 359, 360, 365, 369, 370, 371, 372, 376, 378, 386, 387, 389, 394, 395, 398, 400,
            401, 404, 407, 409, 413, 416, 418, 419, 421, 422, 423, 424, 425, 428, 431, 438, 440,
            442, 447, 450, 452, 453, 457, 458, 462, 467, 480, 484, 488, 490, 492, 498, 507, 509,
            512, 514, 525, 528, 529, 530, 531, 532, 533, 534, 535, 537, 541, 543, 544, 550, 557,
            560, 565, 566, 577, 583, 609, 610, 611, 612, 620, 658, 660, 663, 665, 667, 669, 675,
            677, 679, 680, 681, 684, 688, 692, 693, 696, 699, 701, 706, 707, 709, 710, 712, 713,
            716, 718, 721, 724, 729, 730, 733, 741, 742, 745, 747, 749, 750, 752, 756, 760, 764,
            765, 766, 779, 799, 803, 806, 812, 813, 821, 830, 832, 834, 840, 845, 848, 853, 857,
            859, 860, 861, 862, 866, 869, 872, 873, 878, 879, 884, 885, 887, 889, 891, 892, 894,
            1003, 1010, 1012, 1013
        ] and not attacker.ability() == Ability.LONG_REACH
    
    def selectable_by_mirror_move(self):
        """Whether or not this move can be selected by mirror move."""
        return self.targets_opponent()
        # Previously, this was a hardcoded list of values.
        # I don't think there is any factor besides whether or not the move can target opponents (for single battles).
        """
        return self.id not in [
            10, 14, 54, 68, 74, 96, 97, 100, 102, 104, 105, 106, 107, 110, 111, 112, 113, 114, 115,
            116, 117, 118, 119, 133, 135, 144, 150, 151, 156, 159, 160, 164, 165, 166, 174, 176,
            182, 187, 191, 194, 195, 197, 201, 203, 208, 214, 215, 219, 226, 234, 235, 236, 240,
            241, 243, 244, 248, 254, 255, 256, 258, 264, 266, 267, 268, 270, 272, 273, 274, 275,
            277, 278, 286, 287, 288, 289, 293, 294, 300, 303, 312, 322, 334, 336, 339, 346, 347,
            349, 353, 355, 356, 361, 366, 367, 379, 381, 382, 383, 390, 392, 393, 397, 417, 446,
            455, 456, 461, 468, 469, 470, 471, 475, 476, 483, 489, 495, 501, 502, 504, 505, 508,
            513, 515, 526, 538, 561, 562, 563, 564, 569, 578, 579, 580, 581, 596, 597, 601, 602,
            603, 604, 606, 607, 1000
        ]
        """
    
    def selectable_by_sleep_talk(self):
        """Whether or not this move can be selected by sleep talk."""
        return self.id not in [
            13, 19, 76, 91, 102, 117, 118, 119, 130, 143, 166, 253, 264, 274, 291, 340, 382, 383,
            467, 507, 553, 554, 562, 566, 601, 669, 690, 704, 731
        ]
    
    def selectable_by_assist(self):
        """Whether or not this move can be selected by assist."""
        return self.id not in [
            18, 19, 46, 68, 91, 102, 118, 119, 144, 165, 166, 168, 182, 194, 197, 203, 214, 243,
            264, 266, 267, 270, 271, 289, 291, 340, 343, 364, 382, 383, 415, 448, 467, 476, 507,
            509, 516, 525, 561, 562, 566, 588, 596, 606, 607, 661, 671, 690, 704
        ]
    
    def selectable_by_mimic(self):
        """Whether or not this move can be selected by mimic."""
        return self.id not in [102, 118, 165, 166, 448, 896]
    
    def selectable_by_instruct(self):
        """Whether or not this move can be selected by instruct."""
        return self.id not in [
            13, 19, 63, 76, 91, 102, 117, 118, 119, 130, 143, 144, 165, 166, 214, 264, 267, 274,
            289, 291, 307, 308, 338, 340, 382, 383, 408, 416, 439, 459, 467, 507, 553, 554, 566,
            588, 601, 669, 689, 690, 704, 711, 761, 762, 896
        ]
    
    def selectable_by_snatch(self):
        """Whether or not this move can be selected by snatch."""
        return self.id in [
            14, 54, 74, 96, 97, 104, 105, 106, 107, 110, 111, 112, 113, 115, 116, 133, 135, 151,
            156, 159, 160, 164, 187, 208, 215, 219, 234, 235, 236, 254, 256, 268, 273, 275, 278,
            286, 287, 293, 294, 303, 312, 322, 334, 336, 339, 347, 349, 355, 361, 366, 379, 381,
            392, 393, 397, 417, 455, 456, 461, 468, 469, 475, 483, 489, 501, 504, 508, 526, 538,
            561, 602, 659, 673, 674, 694, 0xCFCF
        ]
    
    @staticmethod
    def get_conversion_2(attacker, defender, battle):
        """
        Gets a random new type for attacker that is resistant to defender's last move type.
        
        Returns a random possible type id, or None if there is no valid type.
        """
        if defender.last_move is None:
            return None
        movetype = defender.last_move.get_type(attacker, defender, battle)
        newtypes = set()
        for e in ElementType:
            if e == ElementType.TYPELESS:
                continue
            if battle.inverse_battle:
                if battle.type_effectiveness[(movetype, e)] > 100:
                    newtypes.add(e)
            else:
                if battle.type_effectiveness[(movetype, e)] < 100:
                    newtypes.add(e)
        newtypes -= set(attacker.type_ids)
        newtypes = list(newtypes)
        if not newtypes:
            return None
        return random.choice(newtypes)
    
    def copy(self):
        """Generate a copy of this move."""
        from moves import Move
        return Move(
            id=self.id,
            identifier=self.name,
            power=self.power,
            pp=self.pp,
            accuracy=self.accuracy,
            priority=self.priority,
            type_id=self.type,
            damage_class_id=self.damage_class,
            effect_id=self.effect,
            effect_chance=self.effect_chance,
            target_id=self.target,
            crit_rate=self.crit_rate,
            min_hits=self.min_hits,
            max_hits=self.max_hits,
        )
    
    @classmethod
    def struggle(cls):
        """Generate an instance of the move struggle."""
        return cls(
            id=165,
            identifier="struggle",
            power=50,
            pp=999999999999,
            accuracy=None,
            priority=0,
            type_id=ElementType.TYPELESS,
            damage_class_id=2,
            effect_id=255,
            effect_chance=None,
            target_id=10,
            crit_rate=0,
            min_hits=None,
            max_hits=None,
        )
    
    @classmethod
    def confusion(cls):
        """Generate an instance of the move confusion."""
        return cls(
            id=0xCFCF,
            identifier="confusion",
            power=40,
            pp=999999999999,
            accuracy=None,
            priority=0,
            type_id=ElementType.TYPELESS,
            damage_class_id=DamageClass.PHYSICAL,
            effect_id=1,
            effect_chance=None,
            target_id=7,
            crit_rate=0,
            min_hits=None,
            max_hits=None,
        )
    
    @classmethod
    def present(cls, power):
        """Generate an instance of the move present."""
        return cls(
            id=217,
            identifier="present",
            power=power,
            pp=999999999999,
            accuracy=90,
            priority=0,
            type_id=ElementType.NORMAL,
            damage_class_id=DamageClass.PHYSICAL,
            effect_id=123,
            effect_chance=None,
            target_id=10,
            crit_rate=0,
            min_hits=None,
            max_hits=None,
        )
    
    def __repr__(self):
        return f"Move(name={self.name!r}, power={self.power!r}, effect_id={self.effect!r})"
