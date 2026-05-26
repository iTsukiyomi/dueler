import random
from ..enums import Ability, DamageClass, ElementType


class MovePower:
    """Power calculation for moves."""

    def get_power(self, attacker, defender, battle):
        """Get the power of this move."""
        # pyrefly: ignore [missing-attribute]
        current_type = self.get_type(attacker, defender, battle)
        # Inflicts damage equal to the user's level.
        # pyrefly: ignore [missing-attribute]
        if self.effect == 88:
            power = attacker.level
        # Inflicts damage between 50% and 150% of the user's level.
        elif self.effect == 89:
            power = random.randint(int(attacker.level * 0.5), int(attacker.level * 1.5))
        # Inflicts more damage to heavier targets, with a maximum of 120 power.
        elif self.effect == 197:
            def_weight = defender.weight(attacker=attacker, move=self)
            if def_weight <= 100:
                power = 20
            elif def_weight <= 250:
                power = 40
            elif def_weight <= 500:
                power = 60
            elif def_weight <= 1000:
                power = 80
            elif def_weight <= 2000:
                power = 100
            else:
                power = 120
        # Power is higher when the user weighs more than the target, up to a maximum of 120.
        elif self.effect == 292:
            weight_delta = attacker.weight() / defender.weight(attacker=attacker, move=self)
            if weight_delta <= 2:
                power = 40
            elif weight_delta <= 3:
                power = 60
            elif weight_delta <= 4:
                power = 80
            elif weight_delta <= 5:
                power = 100
            else:
                power = 120
        # Power increases with happiness, up to a maximum of 102.
        elif self.effect == 122:
            power = int(attacker.happiness / 2.5)
            if power > 102:
                power = 102
            elif power < 1:
                power = 1
        # Power increases as happiness **decreases**, up to a maximum of 102.
        elif self.effect == 124:
            power = int((255 - attacker.happiness) / 2.5)
            if power > 102:
                power = 102
            elif power < 1:
                power = 1
        # Power raises when the user has lower Speed, up to a maximum of 150.
        elif self.effect == 220:
            power = min(150, int(1 + 25 * defender.get_speed(battle) / attacker.get_speed(battle)))
        # Inflicts more damage when the user has more HP remaining, with a maximum of 150 power.
        elif self.effect == 191:
            power = int(150 * (attacker.hp / attacker.starting_hp))
        # Power is 100 times the amount of energy Stockpiled.
        elif self.effect == 162:
            power = 100 * attacker.stockpile
        # Inflicts more damage when the user has less HP remaining, with a maximum of 200 power.
        elif self.effect == 100:
            hp_percent = 64 * (attacker.hp / attacker.starting_hp)
            if hp_percent <= 1:
                power = 200
            elif hp_percent <= 5:
                power = 150
            elif hp_percent <= 12:
                power = 100
            elif hp_percent <= 21:
                power = 80
            elif hp_percent <= 42:
                power = 40
            else:
                power = 20
        # Power increases when this move has less PP, up to a maximum of 200.
        elif self.effect == 236:
            # pyrefly: ignore [missing-attribute]
            if self.pp == 0:
                power = 200
            elif self.pp == 1:
                power = 80
            elif self.pp == 2:
                power = 60
            elif self.pp == 3:
                power = 50
            else:
                power = 40
        # Power increases against targets with more HP remaining, up to a maximum of 120|100 power.
        elif self.effect == 238:
            power = max(1, int(120 * (defender.hp / defender.starting_hp)))
        elif self.effect == 495:
            power = max(1, int(100 * (defender.hp / defender.starting_hp)))
        # Power increases against targets with more raised stats, up to a maximum of 200.
        elif self.effect == 246:
            delta = 0
            delta += max(0, defender.attack_stage)
            delta += max(0, defender.defense_stage)
            delta += max(0, defender.spatk_stage)
            delta += max(0, defender.spdef_stage)
            delta += max(0, defender.speed_stage)
            power = min(200, 60 + (delta * 20))
        # Power is higher when the user has greater Speed than the target, up to a maximum of 150.
        elif self.effect == 294:
            delta = attacker.get_speed(battle) // defender.get_speed(battle)
            if delta <= 0:
                power = 40
            elif delta <= 1:
                power = 60
            elif delta <= 2:
                power = 80
            elif delta <= 3:
                power = 120
            else:
                power = 150
        # Power is higher the more the user's stats have been raised.
        elif self.effect == 306:
            delta = 1
            delta += max(0, attacker.attack_stage)
            delta += max(0, attacker.defense_stage)
            delta += max(0, attacker.spatk_stage)
            delta += max(0, attacker.spdef_stage)
            delta += max(0, attacker.speed_stage)
            delta += max(0, attacker.accuracy_stage)
            delta += max(0, attacker.evasion_stage)
            power = 20 * delta
        # Power doubles every turn this move is used in succession after the first, maxing out after five turns.
        elif self.effect == 120:
            power = (2 ** attacker.fury_cutter) * 10
            attacker.fury_cutter = min(4, attacker.fury_cutter + 1)
        # Power doubles every turn this move is used in succession after the first, resetting after five turns.
        elif self.effect == 118:
            # pyrefly: ignore [missing-attribute]
            power = (2 ** attacker.locked_move.turn) * self.power
        # Power varies randomly from 10 to 150.
        elif self.effect == 127:
            percentile = random.randint(0, 100)
            if percentile <= 5:
                power = 10
            elif percentile <= 15:
                power = 30
            elif percentile <= 35:
                power = 50
            elif percentile <= 65:
                power = 70
            elif percentile <= 85:
                power = 90
            elif percentile <= 95:
                power = 110
            else:
                power = 150
        # Power is based on the user's held item
        elif self.effect == 234:
            power = attacker.held_item.power
        # Power increases by 100% for each consecutive use by any friendly Pokémon, to a maximum of 200.
        elif self.effect == 303:
            power = attacker.echoed_voice_power
        # Power is dependent on the user's held berry.
        elif self.effect == 223:
            if attacker.held_item.get() in (
                "enigma berry", "rowap berry", "maranga berry", "jaboca berry", "belue berry", "kee berry",
                "salac berry", "watmel berry", "lansat berry", "custap berry", "liechi berry", "apicot berry",
                "ganlon berry", "petaya berry", "starf berry", "micle berry", "durin berry"
            ):
                power = 100
            elif attacker.held_item.get() in (
                "cornn berry", "spelon berry", "nomel berry", "wepear berry", "kelpsy berry", "bluk berry",
                "grepa berry", "rabuta berry", "pinap berry", "hondew berry", "pomeg berry", "qualot berry",
                "tamato berry", "magost berry", "pamtre berry", "nanab berry"
            ):
                power = 90
            else:
                power = 80
        elif self.effect == 361 and attacker._name == "Greninja-ash":
            power = 20
        # Power is based on the user's base attack. Only applies when not explicitly overridden.
        # pyrefly: ignore [missing-attribute]
        elif self.effect == 155 and self.power is None:
            power = (attacker.get_raw_attack() // 10) + 5
        # No special changes to power, return its raw value.
        else:
            # pyrefly: ignore [missing-attribute]
            power = self.power
        
        if power is None:
            return None
        
        #NOTE: this needs to be first as it only applies to raw power
        if attacker.ability() == Ability.TECHNICIAN and power <= 60:
            power *= 1.5
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.TOUGH_CLAWS and self.makes_contact(attacker):
            power *= 1.3
        if attacker.ability() == Ability.RIVALRY and "-x" not in (attacker.gender, defender.gender):
            if attacker.gender == defender.gender:
                power *= 1.25
            else:
                power *= .75
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.IRON_FIST and self.is_punching():
            power *= 1.2
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.STRONG_JAW and self.is_biting():
            power *= 1.5
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.MEGA_LAUNCHER and self.is_aura_or_pulse():
            power *= 1.5
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.SHARPNESS and self.is_slicing():
            power *= 1.5
        if attacker.ability() == Ability.RECKLESS and self.effect in (46, 49, 199, 254, 263, 270):
            power *= 1.2
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.TOXIC_BOOST and self.damage_class == DamageClass.PHYSICAL and attacker.nv.poison():
            power *= 1.5
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.FLARE_BOOST and self.damage_class == DamageClass.SPECIAL and attacker.nv.burn():
            power *= 1.5
        if attacker.ability() == Ability.ANALYTIC and defender.has_moved:
            power *= 1.3
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.BATTERY and self.damage_class == DamageClass.SPECIAL:
            power *= 1.3
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.SHEER_FORCE and self.effect_chance is not None: # Not *perfect* but good enough
            power *= 1.3
        if attacker.ability() == Ability.STAKEOUT and defender.swapped_in:
            power *= 2
        if attacker.ability() == Ability.SUPREME_OVERLORD:
            fainted = sum(poke.hp == 0 for poke in attacker.owner.party)
            if fainted:
                power *= (10 + fainted) / 10
        
        # Type buffing abilities - Some use naive type because the type is changed.
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.AERILATE and self.type == ElementType.NORMAL:
            power *= 1.2
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.PIXILATE and self.type == ElementType.NORMAL:
            power *= 1.2
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.GALVANIZE and self.type == ElementType.NORMAL:
            power *= 1.2
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.REFRIGERATE and self.type == ElementType.NORMAL:
            power *= 1.2
        if attacker.ability() == Ability.DRAGONS_MAW and current_type == ElementType.DRAGON:
            power *= 1.5
        if attacker.ability() == Ability.TRANSISTOR and current_type == ElementType.ELECTRIC:
            power *= 1.5
        if attacker.ability() == Ability.WATER_BUBBLE and current_type == ElementType.WATER:
            power *= 2
        if defender.ability(attacker=attacker, move=self) == Ability.WATER_BUBBLE and current_type == ElementType.FIRE:
            power *= .5
        if attacker.ability() == Ability.OVERGROW and current_type == ElementType.GRASS and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.BLAZE and current_type == ElementType.FIRE and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.TORRENT and current_type == ElementType.WATER and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.SWARM and current_type == ElementType.BUG and attacker.hp <= attacker.starting_hp // 3:
            power *= 1.5
        if attacker.ability() == Ability.NORMALIZE and current_type == ElementType.NORMAL:
            power *= 1.2
        if attacker.ability() == Ability.SAND_FORCE and current_type in (ElementType.ROCK, ElementType.GROUND, ElementType.STEEL) and battle.weather.get() == "sandstorm":
            power *= 1.3
        if attacker.ability() in (Ability.STEELWORKER, Ability.STEELY_SPIRIT) and current_type == ElementType.STEEL:
            power *= 1.5
        if attacker.ability() == Ability.ROCKY_PAYLOAD and current_type == ElementType.ROCK:
            power *= 1.5
        
        # Type buffing items
        if attacker.held_item == "black-glasses" and current_type == ElementType.DARK:
            power *= 1.2
        if attacker.held_item == "black-belt" and current_type == ElementType.FIGHTING:
            power *= 1.2
        if attacker.held_item == "hard-stone" and current_type == ElementType.ROCK:
            power *= 1.2
        if attacker.held_item == "magnet" and current_type == ElementType.ELECTRIC:
            power *= 1.2
        if attacker.held_item == "mystic-water" and current_type == ElementType.WATER:
            power *= 1.2
        if attacker.held_item == "never-melt-ice" and current_type == ElementType.ICE:
            power *= 1.2
        if attacker.held_item == "dragon-fang" and current_type == ElementType.DRAGON:
            power *= 1.2
        if attacker.held_item == "poison-barb" and current_type == ElementType.POISON:
            power *= 1.2
        if attacker.held_item == "charcoal" and current_type == ElementType.FIRE:
            power *= 1.2
        if attacker.held_item == "silk-scarf" and current_type == ElementType.NORMAL:
            power *= 1.2
        if attacker.held_item == "metal-coat" and current_type == ElementType.STEEL:
            power *= 1.2
        if attacker.held_item == "sharp-beak" and current_type == ElementType.FLYING:
            power *= 1.2
        if attacker.held_item == "draco-plate" and current_type == ElementType.DRAGON:
            power *= 1.2
        if attacker.held_item == "dread-plate" and current_type == ElementType.DARK:
            power *= 1.2
        if attacker.held_item == "earth-plate" and current_type == ElementType.GROUND:
            power *= 1.2
        if attacker.held_item == "fist-plate" and current_type == ElementType.FIGHTING:
            power *= 1.2
        if attacker.held_item == "flame-plate" and current_type == ElementType.FIRE:
            power *= 1.2
        if attacker.held_item == "icicle-plate" and current_type == ElementType.ICE:
            power *= 1.2
        if attacker.held_item == "insect-plate" and current_type == ElementType.BUG:
            power *= 1.2
        if attacker.held_item == "iron-plate" and current_type == ElementType.STEEL:
            power *= 1.2
        if attacker.held_item == "meadow-plate" and current_type == ElementType.GRASS:
            power *= 1.2
        if attacker.held_item == "mind-plate" and current_type == ElementType.PSYCHIC:
            power *= 1.2
        if attacker.held_item == "pixie-plate" and current_type == ElementType.FAIRY:
            power *= 1.2
        if attacker.held_item == "sky-plate" and current_type == ElementType.FLYING:
            power *= 1.2
        if attacker.held_item == "splash-plate" and current_type == ElementType.WATER:
            power *= 1.2
        if attacker.held_item == "spooky-plate" and current_type == ElementType.GHOST:
            power *= 1.2
        if attacker.held_item == "stone-plate" and current_type == ElementType.ROCK:
            power *= 1.2
        if attacker.held_item == "toxic-plate" and current_type == ElementType.POISON:
            power *= 1.2
        if attacker.held_item == "zap-plate" and current_type == ElementType.ELECTRIC:
            power *= 1.2
        if attacker.held_item == "adamant-orb" and current_type in (ElementType.DRAGON, ElementType.STEEL) and attacker._name == "Dialga":
            power *= 1.2
        if attacker.held_item == "griseous-orb" and current_type in (ElementType.DRAGON, ElementType.GHOST) and attacker._name == "Giratina":
            power *= 1.2
        if attacker.held_item == "soul-dew" and current_type in (ElementType.DRAGON, ElementType.PSYCHIC) and attacker._name in ("Latios", "Latias"):
            power *= 1.2
        if attacker.held_item == "lustrous-orb" and current_type in (ElementType.DRAGON, ElementType.WATER) and attacker._name == "Palkia":
            power *= 1.2
        
        # Damage class buffing items
        # pyrefly: ignore [missing-attribute]
        if attacker.held_item == "wise-glasses" and self.damage_class == DamageClass.SPECIAL:
            power *= 1.1
        # pyrefly: ignore [missing-attribute]
        if attacker.held_item == "muscle-band" and self.damage_class == DamageClass.PHYSICAL:
            power *= 1.1

        # If there be weather, this move has doubled power and the weather's type.
        if self.effect == 204 and battle.weather.get() in ("hail", "sandstorm", "rain", "h-rain", "sun", "h-sun"):
            power *= 2
        # During hail, rain-dance, or sandstorm, power is halved.
        if self.effect == 152 and battle.weather.get() in ("rain", "hail"):
            power *= 0.5
        # Power doubles if user is burned, paralyzed, or poisoned.
        if self.effect == 170 and (attacker.nv.burn() or attacker.nv.poison() or attacker.nv.paralysis()):
            power *= 2
        # If the target is paralyzed, power is doubled and cures the paralysis.
        if self.effect == 172 and defender.nv.paralysis():
            power *= 2
            defender.nv.reset()
        # If the target is poisoned, this move has double power.
        if self.effect in (284, 461) and defender.nv.poison():
            power *= 2
        # If the target is sleeping, this move has double power, and the target wakes up.
        if self.effect == 218 and defender.nv.sleep():
            power *= 2
            defender.nv.reset()
        # Has double power against Pokémon that have less than half their max HP remaining.
        if self.effect == 222 and defender.hp < defender.starting_hp // 2:
            power *= 2
        # Power is doubled if the target has already moved this turn.
        if self.effect == 231 and defender.has_moved:
            power *= 2
        # Has double power if the target has a major status ailment.
        if self.effect == 311 and defender.nv.current:
            power *= 2
        # If the user has used defense-curl since entering the field, this move has double power.
        if self.effect == 118 and attacker.defense_curl:
            power *= 2
        # Has double power if the user's last move failed.
        if self.effect == 409 and attacker.last_move_failed:
            power *= 2
        # Has double power if the target is in the first turn of dive.
        if self.effect in (258, 262) and defender.dive:
            power *= 2
        # Has double power if the target is in the first turn of dig.
        if self.effect in (127, 148) and defender.dig:
            power *= 2
        # Has double power if the target is in the first turn of bounce or fly.
        if self.effect in (147, 150) and defender.fly:
            power *= 2
        # Has double power if the user takes damage before attacking this turn.
        if self.effect == 186 and attacker.last_move_damage is not None:
            power *= 2
        # Has double power if the user has no held item.
        if self.effect == 318 and not attacker.held_item.has_item():
            power *= 2
        # Has double power if a friendly Pokémon fainted last turn.
        if self.effect == 320 and attacker.owner.retaliate.active():
            power *= 2
        # Has double power against, and can hit, Pokémon attempting to switch out.
        if self.effect == 129 and (isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.effect in (128, 154, 229, 347, 493)):
            power *= 2
        # Power is doubled if the target has already received damage this turn.
        if self.effect == 232 and defender.dmg_this_turn:
            power *= 2
        # Power is doubled if the target is minimized.
        if self.effect == 151 and defender.minimized:
            power *= 2
        # With Fusion Bolt, power is doubled.
        if self.effect == 336 and battle.last_move_effect == 337:
            power *= 2
        # With Fusion Flare, power is doubled.
        if self.effect == 337 and battle.last_move_effect == 336:
            power *= 2
        # Me first increases the power of the used move by 50%.
        if attacker.owner.selected_action is not None and not isinstance(attacker.owner.selected_action, int) and attacker.owner.selected_action.effect == 242:
            power *= 1.5
        # Has 1.5x power during gravity.
        if self.effect == 435 and battle.gravity.active():
            power *= 1.5
        # If the user attacks before the target, or if the target switched in this turn, its base power doubles.
        if self.effect == 436 and (not defender.has_moved or defender.swapped_in):
            power *= 2
        # If the terrain is psychic and the user is grounded, this move gets 1.5x power.
        if self.effect == 440 and battle.terrain.item == "psychic" and attacker.grounded(battle):
            power *= 1.5
        # Power is doubled if terrain is present.
        if self.effect == 441 and battle.terrain.item and attacker.grounded(battle):
            power *= 2
        # Power is boosted by 50% if used on a Pokémon that is holding an item that can be knocked off.
        if self.effect == 189 and defender.held_item.has_item() and defender.held_item.can_remove():
            power *= 1.5
        # If the target is under the effect of electric terrain, this move has double power.
        if self.effect == 443 and battle.terrain.item == "electric" and defender.grounded(battle, attacker=attacker, move=self):
            power *= 2
        # Deals 1.5x damage if the user is under the effect of misty terrain.
        if self.effect == 444 and battle.terrain.item == "misty" and attacker.grounded(battle):
            power *= 1.5
        # Power is doubled if any of the user's stats were lowered this turn.
        if self.effect == 450 and attacker.stat_decreased:
            power *= 2
        # Power is doubled if the defender has a non volatile status effect.
        if self.effect == 465 and defender.nv.current:
            power *= 2
        # Deals 4/3x damage if supereffective.
        if self.effect == 482 and defender.effectiveness(current_type, battle, attacker=attacker, move=self) > 1:
            power *= 4/3
        # Power is multiplied by (1 + number of fainted party members)x, capping at 101x (100 faints).
        if self.effect == 490:
            power *= 1 + min(attacker.owner.num_fainted, 100)
        # Power is multiplied by (1 + number of times hit)x, capping at 7x (6 hits).
        if self.effect == 491:
            power *= 1 + min(attacker.num_hits, 6)
        # Has a 30% chance to double power
        if self.effect == 498 and random.random() <= 0.3:
            power *= 2

        # Terrains
        if battle.terrain.item == "psychic" and attacker.grounded(battle) and current_type == ElementType.PSYCHIC:
            power *= 1.3
        if battle.terrain.item == "grassy" and attacker.grounded(battle) and current_type == ElementType.GRASS:
            power *= 1.3
        # pyrefly: ignore [missing-attribute]
        if battle.terrain.item == "grassy" and defender.grounded(battle, attacker=attacker, move=self) and self.id in (89, 222, 523):
            power *= 0.5
        if battle.terrain.item == "electric" and attacker.grounded(battle) and current_type == ElementType.ELECTRIC:
            power *= 1.3
        if battle.terrain.item == "misty" and defender.grounded(battle, attacker=attacker, move=self) and current_type == ElementType.DRAGON:
            power *= 0.5
            
        # Power buffing statuses
        if attacker.charge.active() and current_type == ElementType.ELECTRIC:
            power *= 2
        if (attacker.owner.mud_sport.active() or defender.owner.mud_sport.active()) and current_type == ElementType.ELECTRIC:
            power //= 3
        if (attacker.owner.water_sport.active() or defender.owner.water_sport.active()) and current_type == ElementType.FIRE:
            power //= 3

        return int(power)
