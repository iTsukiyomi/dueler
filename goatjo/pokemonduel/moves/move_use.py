import random
from ..misc import LockedMove
from ..enums import Ability, ElementType, MoveTarget


class MoveUse:
    """Main move execution logic."""

    def use(self, attacker, defender, battle, *, use_pp=True, override_sleep=False, bounced=False):
        """
        Uses this move as attacker on defender.
        
        Returns a string of formatted results of the move.
        """
        #This handles an edge case for moves that cause the target to swap out
        if attacker.has_moved and use_pp:
            return ""
        self.used = True
        if use_pp:
            attacker.has_moved = True
            attacker.last_move = self
            attacker.beak_blast = False
            attacker.destiny_bond = False
            # Reset semi-invulnerable status in case this is turn 2
            attacker.dive = False
            attacker.dig = False
            attacker.fly = False
            attacker.shadow_force = False
        current_type = self.get_type(attacker, defender, battle)
        effect_chance = self.get_effect_chance(attacker, defender, battle)
        msg = ""

        if self.effect in (5, 126, 168, 254, 336, 398, 458, 500) and attacker.nv.freeze():
            attacker.nv.reset()
            msg += f"{attacker.name} thawed out!\n"
        if attacker.nv.freeze():
            if use_pp and not random.randint(0, 4):
                attacker.nv.reset()
                msg += f"{attacker.name} is no longer frozen!\n"
            else:
                msg += f"{attacker.name} is frozen solid!\n"
                if self.effect == 28:
                    attacker.locked_move = None
                return msg
        if attacker.nv.paralysis() and not random.randint(0, 3):
            msg += f"{attacker.name} is paralyzed! It can't move!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.infatuated is defender and not random.randint(0, 1):
            msg += f"{attacker.name} is in love with {defender.name} and can't bare to hurt them!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.flinched:
            msg += f"{attacker.name} flinched! It can't move!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.nv.sleep():
            if use_pp and attacker.nv.sleep_timer.next_turn():
                attacker.nv.reset()
                msg += f"{attacker.name} woke up!\n"
            elif self.effect not in (93, 98) and attacker.ability() != Ability.COMATOSE and not override_sleep:
                msg += f"{attacker.name} is fast asleep!\n"
                if self.effect == 28:
                    attacker.locked_move = None
                return msg 
        if attacker.confusion.next_turn():
            msg += f"{attacker.name} is no longer confused!\n"
        if attacker.confusion.active() and not random.randint(0, 2):
            msg += f"{attacker.name} hurt itself in its confusion!\n"
            msgadd, numhits = self.confusion().attack(attacker, attacker, battle)
            msg += msgadd
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        if attacker.ability() == Ability.TRUANT and attacker.truant_turn % 2:
            msg += f"{attacker.name} is loafing around!\n"
            if self.effect == 28:
                attacker.locked_move = None
            return msg
        
        if not bounced:
            msg += f"{attacker.name} used {self.pretty_name}!\n"
            attacker.metronome.use(self.name)
        
        # PP
        if attacker.locked_move is None and use_pp:
            self.pp -= 1
            if defender.ability(attacker=attacker, move=self) == Ability.PRESSURE and self.pp != 0:
                if self.targets_opponent() or self.effect in (113, 193, 196, 250, 267):
                    self.pp -= 1
            if self.pp == 0:
                msg += "It ran out of PP!\n"

        #User is using a choice item and had not used a move yet, set that as their only move.
        if attacker.choice_move is None and use_pp:
            if attacker.held_item in ("choice-scarf", "choice-band", "choice-specs"):
                attacker.choice_move = self
            elif attacker.ability() == Ability.GORILLA_TACTICS:
                attacker.choice_move = self

        # Stance change
        if attacker.ability() == Ability.STANCE_CHANGE:
            if attacker._name == "Aegislash" and self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
                if attacker.form("Aegislash-blade"):
                    msg += f"{attacker.name} draws its blade!\n"
            if attacker._name == "Aegislash-blade" and self.effect == 356:
                if attacker.form("Aegislash"):
                    msg += f"{attacker.name} readies its shield!\n"

        # Powder damage
        if attacker.powdered and current_type == ElementType.FIRE and battle.weather.get() != "h-rain":
            msg += attacker.damage(attacker.starting_hp // 4, battle, source="its powder exploding")
            return msg

        # Snatch steal
        if defender.snatching and self.selectable_by_snatch():
            msg += f"{defender.name} snatched the move!\n"
            msg += self.use(defender, attacker, battle, use_pp=False)
            return msg

        # Check Fail
        if not self.check_executable(attacker, defender, battle):
            msg += "But it failed!\n"
            if self.effect in (28, 118):
                attacker.locked_move = None
            attacker.last_move_failed = True
            return msg
        
        # Setup for multi-turn moves
        if attacker.locked_move is None:
            # 2 turn moves
            # During sun, this move does not need to charge
            if self.effect == 152 and battle.weather.get() not in ("sun", "h-sun"):
                attacker.locked_move = LockedMove(self, 2)
            # During rain, this move does not need to charge
            if self.effect == 502:
                if battle.weather.get() not in ("rain", "h-rain"):
                    attacker.locked_move = LockedMove(self, 2)
                else:
                    # If this move isn't charging, the spatk increase has to happen manually
                    msg += attacker.append_spatk(1, attacker=attacker, move=self)
            if self.effect in (40, 76, 81, 146, 156, 256, 257, 264, 273, 332, 333, 366, 451):
                attacker.locked_move = LockedMove(self, 2)
            # 3 turn moves
            if self.effect == 27:
                attacker.locked_move = LockedMove(self, 3)
                attacker.bide = 0
            if self.effect == 160:
                attacker.locked_move = LockedMove(self, 3)
                attacker.uproar.set_turns(3)
                if attacker.nv.sleep():
                    attacker.nv.reset()
                    msg += f"{attacker.name} woke up!\n"
                if defender.nv.sleep():
                    defender.nv.reset()
                    msg += f"{defender.name} woke up!\n"
            # 5 turn moves
            if self.effect == 118:
                attacker.locked_move = LockedMove(self, 5)
            # 2-3 turn moves
            if self.effect == 28:
                attacker.locked_move = LockedMove(self, random.randint(2, 3))
            #2-5 turn moves
            if self.effect == 160:
                attacker.locked_move = LockedMove(self, random.randint(2, 5))
            # Semi-invulnerable
            if self.effect == 256:
                attacker.dive = True
            if self.effect == 257:
                attacker.dig = True
            if self.effect in (156, 264):
                attacker.fly = True
            if self.effect == 273:
                attacker.shadow_force = True
        
        # Early exits for moves that hit a certain turn when it is not that turn
        # Turn 1 hit moves
        if self.effect == 81 and attacker.locked_move:
            if attacker.locked_move.turn != 0:
                msg += "It's recharging!\n"
                return msg
        
        # Turn 2 hit moves
        elif self.effect in (40, 76, 146, 152, 156, 256, 257, 264, 273, 332, 333, 366, 451, 502) and attacker.locked_move:
            if attacker.locked_move.turn != 1:
                if self.effect == 146:
                    msg += attacker.append_defense(1, attacker=attacker, move=self)
                elif self.effect in (451, 502):
                    msg += attacker.append_spatk(1, attacker=attacker, move=self)
                else:
                    msg += "It's charging up!\n"
                    # Gulp Missile
                    if self.effect == 256 and attacker.ability() == Ability.GULP_MISSILE and attacker._name == "Cramorant":
                        if attacker.hp > attacker.starting_hp // 2:
                            if attacker.form("Cramorant-gulping"):
                                msg += f"{attacker.name} gulped up an arrokuda!\n"
                        else:
                            if attacker.form("Cramorant-gorging"):
                                msg += f"{attacker.name} gulped up a pikachu!\n"
                return msg
        
        # Turn 3 hit moves
        elif self.effect == 27:
            if attacker.locked_move.turn != 2:
                msg += "It's storing energy!\n"
                return msg
        
        # User Faints
        if self.effect in (8, 444):
            msg += attacker.faint(battle)

        # User takes damage
        if self.effect == 420:
            msg += attacker.damage(attacker.starting_hp // 2, battle, source="its head exploding (tragic)")
        
        # User's type changes
        if current_type != ElementType.TYPELESS:
            if attacker.ability() == Ability.PROTEAN:
                attacker.type_ids = [current_type]
                t = ElementType(current_type).name.lower()
                msg += f"{attacker.name} transformed into a {t} type using its protean!\n"
            if attacker.ability() == Ability.LIBERO:
                attacker.type_ids = [current_type]
                t = ElementType(current_type).name.lower()
                msg += f"{attacker.name} transformed into a {t} type using its libero!\n"
        
        # Status effects reflected by magic coat or magic bounce.
        if self.is_affected_by_magic_coat() and (defender.ability(attacker=attacker, move=self) == Ability.MAGIC_BOUNCE or defender.magic_coat) and not bounced:
            msg += f"It was reflected by {defender.name}'s magic bounce!\n"
            hm = defender.has_moved
            msg += self.use(defender, attacker, battle, use_pp=False, bounced=True)
            defender.has_moved = hm
            return msg
        
        # Check Effect
        if not self.check_effective(attacker, defender, battle) and not bounced:
            msg += "It had no effect...\n"
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            attacker.last_move_failed = True
            return msg
        
        # Check Semi-invulnerable - treated as a miss
        if not self.check_semi_invulnerable(attacker, defender, battle):
            msg += f"{defender.name} avoided the attack!\n"
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            return msg
        
        # Check Protection
        was_hit, msgdelta = self.check_protect(attacker, defender, battle)
        if not was_hit:
            msg += f"{defender.name} was protected against the attack!\n"
            msg += msgdelta
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            return msg
        
        # Check Hit
        if not self.check_hit(attacker, defender, battle):
            msg += "But it missed!\n"
            if self.effect == 120:
                attacker.fury_cutter = 0
            if self.effect in (46, 478):
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="recoil")
            if self.effect in (28, 81, 118):
                attacker.locked_move = None
            return msg
        
        # Absorbs
        if self.targets_opponent() and self.effect != 459:
            # Heal
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.VOLT_ABSORB:
                msg += f"{defender.name}'s volt absorb absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) == Ability.WATER_ABSORB:
                msg += f"{defender.name}'s water absorb absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) == Ability.DRY_SKIN:
                msg += f"{defender.name}'s dry skin absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            if current_type == ElementType.GROUND and defender.ability(attacker=attacker, move=self) == Ability.EARTH_EATER:
                msg += f"{defender.name}'s earth eater absorbed the move!\n"
                msg += defender.heal(defender.starting_hp // 4, source="absorbing the move")
                return msg
            # Stat stage changes
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.LIGHTNING_ROD:
                msg += f"{defender.name}'s lightning rod absorbed the move!\n"
                msg += defender.append_spatk(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.ELECTRIC and defender.ability(attacker=attacker, move=self) == Ability.MOTOR_DRIVE:
                msg += f"{defender.name}'s motor drive absorbed the move!\n"
                msg += defender.append_speed(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.WATER and defender.ability(attacker=attacker, move=self) == Ability.STORM_DRAIN:
                msg += f"{defender.name}'s storm drain absorbed the move!\n"
                msg += defender.append_spatk(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.GRASS and defender.ability(attacker=attacker, move=self) == Ability.SAP_SIPPER:
                msg += f"{defender.name}'s sap sipper absorbed the move!\n"
                msg += defender.append_attack(1, attacker=defender, move=self)
                return msg
            if current_type == ElementType.FIRE and defender.ability(attacker=attacker, move=self) == Ability.WELL_BAKED_BODY:
                msg += f"{defender.name}'s well baked body absorbed the move!\n"
                msg += defender.append_defense(2, attacker=defender, move=self)
                return msg
            # Other
            if current_type == ElementType.FIRE and defender.ability(attacker=attacker, move=self) == Ability.FLASH_FIRE:
                defender.flash_fire = True
                msg += f"{defender.name} used its flash fire to buff its fire type moves!\n"
                return msg
        
        # Stat stage from type items
        if not defender.substitute:
            if current_type == ElementType.WATER and defender.held_item == "absorb-bulb":
                msg += defender.append_spatk(1, attacker=defender, move=self, source="its absorb bulb")
                defender.held_item.use()
            if current_type == ElementType.ELECTRIC and defender.held_item == "cell-battery":
                msg += defender.append_attack(1, attacker=defender, move=self, source="its cell battery")
                defender.held_item.use()
            if current_type == ElementType.WATER and defender.held_item == "luminous-moss":
                msg += defender.append_spdef(1, attacker=defender, move=self, source="its luminous moss")
                defender.held_item.use()
            if current_type == ElementType.ICE and defender.held_item == "snowball":
                msg += defender.append_attack(1, attacker=defender, move=self, source="its snowball")
                defender.held_item.use()

        # Metronome
        if self.effect == 84:
            attacker.has_moved = False
            raw = random.choice(battle.metronome_moves_raw)
            msg += Move(**raw).use(attacker, defender, battle)
            return msg
        
        # Brick break - runs before damage calculation
        if self.effect == 187:
            if defender.owner.aurora_veil.active():
                defender.owner.aurora_veil.set_turns(0)
                msg += f"{defender.name}'s aurora veil wore off!\n"
            if defender.owner.light_screen.active():
                defender.owner.light_screen.set_turns(0)
                msg += f"{defender.name}'s light screen wore off!\n"
            if defender.owner.reflect.active():
                defender.owner.reflect.set_turns(0)
                msg += f"{defender.name}'s reflect wore off!\n"
        
        # Sleep talk
        if self.effect == 98:
            move = random.choice([m for m in attacker.moves if m.selectable_by_sleep_talk()])
            msg += move.use(attacker, defender, battle, use_pp=False, override_sleep=True)
            return msg
        
        # Mirror Move/Copy Cat
        if self.effect in (10, 243):
            msg += defender.last_move.use(attacker, defender, battle, use_pp=False)
            return msg
        
        # Me First
        if self.effect == 242:
            msg += defender.owner.selected_action.use(attacker, defender, battle, use_pp=False)
            return msg
        
        # Assist
        if self.effect == 181:
            msg += attacker.get_assist_move().use(attacker, defender, battle, use_pp=False)
            return msg
        
        # Spectral Thief
        if self.effect == 410:
            if defender.attack_stage > 0:
                stage = defender.attack_stage
                defender.attack_stage = 0
                msg += f"{defender.name}'s attack stage was reset!\n"
                msg += attacker.append_attack(stage, attacker=attacker, move=self)
            if defender.defense_stage > 0:
                stage = defender.defense_stage
                defender.defense_stage = 0
                msg += f"{defender.name}'s defense stage was reset!\n"
                msg += attacker.append_defense(stage, attacker=attacker, move=self)
            if defender.spatk_stage > 0:
                stage = defender.spatk_stage
                defender.spatk_stage = 0
                msg += f"{defender.name}'s special attack stage was reset!\n"
                msg += attacker.append_spatk(stage, attacker=attacker, move=self)
            if defender.spdef_stage > 0:
                stage = defender.spdef_stage
                defender.spdef_stage = 0
                msg += f"{defender.name}'s special defense stage was reset!\n"
                msg += attacker.append_spdef(stage, attacker=attacker, move=self)
            if defender.speed_stage > 0:
                stage = defender.speed_stage
                defender.speed_stage = 0
                msg += f"{defender.name}'s speed stage was reset!\n"
                msg += attacker.append_speed(stage, attacker=attacker, move=self)
            if defender.evasion_stage > 0:
                stage = defender.evasion_stage
                defender.evasion_stage = 0
                msg += f"{defender.name}'s evasion stage was reset!\n"
                msg += attacker.append_evasion(stage, attacker=attacker, move=self)
            if defender.accuracy_stage > 0:
                stage = defender.accuracy_stage
                defender.accuracy_stage = 0
                msg += f"{defender.name}'s accuracy stage was reset!\n"
                msg += attacker.append_accuracy(stage, attacker=attacker, move=self) 
        
        # Future Sight
        if self.effect == 149:
            defender.owner.future_sight.set((attacker, self), 3)
            msg += f"{attacker.name} foresaw an attack!\n"
            return msg
        
        # Present
        if self.effect == 123:
            action = random.randint(1, 4)
            if action == 1:
                if defender.hp == defender.starting_hp:
                    msg += "It had no effect!\n"
                else:
                    msg += defender.heal(defender.starting_hp // 4, source=f"{attacker.name}'s present")
                return msg
            if action == 2:
                power = 40
            elif action == 3:
                power = 80
            else:
                power = 120
            m = self.present(power)
            msgadd, _ = m.attack(attacker, defender, battle)
            msg += msgadd
            return msg
        
        # Incinerate
        if self.effect == 315 and defender.held_item.is_berry(only_active=False):
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                defender.held_item.remove()
                msg += f"{defender.name}'s berry was incinerated!\n"
        
        # Poltergeist 
        if self.effect == 446:
            msg += f"{defender.name} is about to be attacked by its {defender.held_item.get()}!\n"
        
        numhits = 0
        # Turn 1 hit moves
        if self.effect == 81 and attacker.locked_move:
            if attacker.locked_move.turn == 0:
                msgadd, numhits = self.attack(attacker, defender, battle)
                msg += msgadd
                
        # Turn 2 hit moves
        elif self.effect in (40, 76, 146, 152, 156, 256, 257, 264, 273, 332, 333, 366, 451, 502) and attacker.locked_move:
            if attacker.locked_move.turn == 1:
                if self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
                    msgadd, numhits = self.attack(attacker, defender, battle)
                    msg += msgadd
                
        # Turn 3 hit moves
        elif self.effect == 27:
            if attacker.locked_move.turn == 2:
                msg += defender.damage(attacker.bide * 2, battle, move=self, move_type=current_type, attacker=attacker)
                attacker.bide = None
                numhits = 1
        
        # Counter attack moves
        elif self.effect == 228:
            msg += defender.damage(int(1.5 * attacker.last_move_damage[0]), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 145:
            msg += defender.damage(2 * attacker.last_move_damage[0], battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 90:
            msg += defender.damage(2 * attacker.last_move_damage[0], battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        
        # Static-damage moves
        elif self.effect == 41:
            msg += defender.damage(defender.hp // 2, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 42:
            msg += defender.damage(40, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 88:
            msg += defender.damage(attacker.level, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 89:
            # 0.5-1.5, increments of .1
            scale = (random.randint(0, 10) / 10.0) + .5
            msg += defender.damage(int(attacker.level * scale), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 131:
            msg += defender.damage(20, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 190:
            msg += defender.damage(max(0, defender.hp - attacker.hp), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 39:
            msg += defender.damage(defender.hp, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 321:
            msg += defender.damage(attacker.hp, battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        elif self.effect == 413:
            msg += defender.damage(3 * (defender.hp // 4), battle, move=self, move_type=current_type, attacker=attacker)
            numhits = 1
        
        # Beat up, a stupid move
        elif self.effect == 155:
            for poke in attacker.owner.party:
                if defender.hp == 0:
                    break
                if poke.hp == 0:
                    continue
                if poke is attacker:
                    msgadd, nh = self.attack(attacker, defender, battle)
                    msg += msgadd
                    numhits += nh
                else:
                    if poke.nv.current:
                        continue
                    fake_move = {
                        "id": 251,
                        "identifier": "beat-up",
                        "power": (poke.get_raw_attack() // 10) + 5,
                        "pp": 100,
                        "accuracy": 100,
                        "priority": 0,
                        "type_id": ElementType.DARK,
                        "damage_class_id": DamageClass.PHYSICAL,
                        "effect_id": 1,
                        "effect_chance": None,
                        "target_id": 10,
                        "crit_rate": 0,
                        "min_hits": None,
                        "max_hits": None,
                    }
                    fake_move = Move(**fake_move)
                    msgadd, nh = fake_move.attack(attacker, defender, battle)
                    msg += msgadd
                    numhits += nh
        
        # Other damaging moves
        elif self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
            msgadd, numhits = self.attack(attacker, defender, battle)
            msg += msgadd
        
        # Fusion Flare/Bolt effect tracking
        battle.last_move_effect = self.effect
        
        # Stockpile
        if self.effect == 161:
            attacker.stockpile += 1
            msg += f"{attacker.name} stores energy!\n"
        if self.effect == 162:
            msg += attacker.append_defense(-attacker.stockpile, attacker=attacker, move=self)
            msg += attacker.append_spdef(-attacker.stockpile, attacker=attacker, move=self)
            attacker.stockpile = 0

        # Healing
        if self.effect in (33, 215):
            msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect in (434, 457):
            msg += attacker.heal(attacker.starting_hp // 4)
        if self.effect == 310:
            if attacker.ability() == Ability.MEGA_LAUNCHER:
                msg += defender.heal((defender.starting_hp * 3) // 4)
            else:
                msg += defender.heal(defender.starting_hp // 2)
        if self.effect == 133:
            if battle.weather.get() in ("sun", "h-sun"):
                msg += attacker.heal((attacker.starting_hp * 2) // 3)
            elif battle.weather.get() == "h-wind":
                msg += attacker.heal(attacker.starting_hp // 2)
            elif battle.weather.get():
                msg += attacker.heal(attacker.starting_hp // 4)
            else:
                msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect == 85:
            defender.leech_seed = True
            msg += f"{defender.name} was seeded!\n"
        if self.effect == 163:
            msg += attacker.heal(attacker.starting_hp // {1: 4, 2: 2, 3: 1}[attacker.stockpile], source="stockpiled energy")
            msg += attacker.append_defense(-attacker.stockpile, attacker=attacker, move=self)
            msg += attacker.append_spdef(-attacker.stockpile, attacker=attacker, move=self)
            attacker.stockpile = 0
        if self.effect == 180:
            attacker.owner.wish.set(attacker.starting_hp // 2)
            msg += f"{attacker.name} makes a wish!\n"
        if self.effect == 382:
            if battle.weather.get() == "sandstorm":
                msg += attacker.heal((attacker.starting_hp * 2) // 3)
            else:
                msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect == 387:
            if battle.terrain.item == "grassy":
                msg += attacker.heal((attacker.starting_hp * 2) // 3)
            else:
                msg += attacker.heal(attacker.starting_hp // 2)
        if self.effect == 388:
            msg += attacker.heal(defender.get_attack(battle))
        if self.effect == 400:
            status = defender.nv.current
            defender.nv.reset()
            msg += f"{defender.name}'s {status} was healed!\n"
            msg += attacker.heal(attacker.starting_hp // 2)

        # Status effects
        if self.effect in (5, 126, 201, 254, 274, 333, 365, 458, 465, 500):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
        if self.effect == 168:
            msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
        if self.effect == 429 and defender.stat_increased:
            msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
        if self.effect == 37:
            status = random.choice(["burn", "freeze", "paralysis"])
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status(status, battle, attacker=attacker, move=self)
        if self.effect == 464:
            status = random.choice(["poison", "paralysis", "sleep"])
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status(status, battle, attacker=attacker, move=self)
        if self.effect in (6, 261, 275, 380):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("freeze", battle, attacker=attacker, move=self)
        if self.effect in (7, 153, 263, 264, 276, 332, 372, 396):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
        if self.effect == 68:
            msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
        if self.effect in (3, 78, 210, 447, 461):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("poison", battle, attacker=attacker, move=self)
        if self.effect in (67, 390, 486):
            msg += defender.nv.apply_status("poison", battle, attacker=attacker, move=self)
        if self.effect == 203:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("b-poison", battle, attacker=attacker, move=self)
        if self.effect == 34:
            msg += defender.nv.apply_status("b-poison", battle, attacker=attacker, move=self)
        if self.effect == 2:
            if self.id == 464 and attacker._name != "Darkrai":
                msg += f"{attacker.name} can't use the move!\n"
            else:
                msg += defender.nv.apply_status("sleep", battle, attacker=attacker, move=self)
        if self.effect == 330:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.nv.apply_status("sleep", battle, attacker=attacker, move=self)
        if self.effect == 38:
            msg += attacker.nv.apply_status("sleep", battle, attacker=attacker, move=self, turns=3, force=True)
            if attacker.nv.sleep():
                msg += f"{attacker.name}'s slumber restores its health back to full!\n"
                attacker.hp = attacker.starting_hp
        if self.effect in (50, 119, 167, 200):
            msg += defender.confuse(attacker=attacker, move=self)
        # This checks if attacker.locked_move is not None as locked_move is cleared if the poke dies to rocky helmet or similar items
        if self.effect == 28 and attacker.locked_move is not None and attacker.locked_move.is_last_turn():
            msg += attacker.confuse()
        if self.effect in (77, 268, 334, 478):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.confuse(attacker=attacker, move=self)
        if self.effect == 497 and defender.stat_increased:
            msg += defender.confuse(attacker=attacker, move=self)
        if self.effect in (194, 457, 472):
            attacker.nv.reset()
            msg += f"{attacker.name}'s status was cleared!\n"
        if self.effect == 386:
            if defender.nv.burn():
                defender.nv.reset()
                msg += f"{defender.name}'s burn was healed!\n"
        
        # Stage changes
        # +1
        if self.effect in (11, 209, 213, 278, 313, 323, 328, 392, 414, 427, 468, 472, 487):
            msg += attacker.append_attack(1, attacker=attacker, move=self)
        if self.effect in (12, 157, 161, 207, 209, 323, 367, 414, 427, 467, 468, 472):
            msg += attacker.append_defense(1, attacker=attacker, move=self)
        if self.effect in (14, 212, 291, 328, 392, 414, 427, 472):
            msg += attacker.append_spatk(1, attacker=attacker, move=self)
        if self.effect in (161, 175, 207, 212, 291, 367, 414, 427, 472):
            msg += attacker.append_spdef(1, attacker=attacker, move=self)
        if self.effect in (130, 213, 291, 296, 414, 427, 442, 468, 469, 487):
            msg += attacker.append_speed(1, attacker=attacker, move=self)
        if self.effect in (17, 467):
            msg += attacker.append_evasion(1, attacker=attacker, move=self)
        if self.effect in (278, 323):
            msg += attacker.append_accuracy(1, attacker=attacker, move=self)
        if self.effect == 139:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_defense(1, attacker=attacker, move=self)
        if self.effect in (140, 375):
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_attack(1, attacker=attacker, move=self)
        if self.effect == 277:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_spatk(1, attacker=attacker, move=self)
        if self.effect == 433:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_speed(1, attacker=attacker, move=self)
        if self.effect == 167:
            msg += defender.append_spatk(1, attacker=attacker, move=self)
        # +2
        if self.effect in (51, 309):
            msg += attacker.append_attack(2, attacker=attacker, move=self)
        if self.effect in (52, 453):
            msg += attacker.append_defense(2, attacker=attacker, move=self)
        if self.effect in (53, 285, 309, 313, 366):
            msg += attacker.append_speed(2, attacker=attacker, move=self)
        if self.effect in (54, 309, 366):
            msg += attacker.append_spatk(2, attacker=attacker, move=self)
        if self.effect in (55, 366):
            msg += attacker.append_spdef(2, attacker=attacker, move=self)
        if self.effect == 109:
            msg += attacker.append_evasion(2, attacker=attacker, move=self)
        if self.effect in (119, 432, 483):
            msg += defender.append_attack(2, attacker=attacker, move=self)
        if self.effect == 432:
            msg += defender.append_spatk(2, attacker=attacker, move=self)
        if self.effect == 359:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_defense(2, attacker=attacker, move=self)
        # -1
        if self.effect in (19, 206, 344, 347, 357, 365, 388, 412):
            msg += defender.append_attack(-1, attacker=attacker, move=self)
        if self.effect in (20, 206):
            msg += defender.append_defense(-1, attacker=attacker, move=self)
        if self.effect in (344, 347, 358, 412):
            msg += defender.append_spatk(-1, attacker=attacker, move=self)
        if self.effect == 428:
            msg += defender.append_spdef(-1, attacker=attacker, move=self)
        if self.effect in (331, 390):
            msg += defender.append_speed(-1, attacker=attacker, move=self)
        if self.effect == 24:
            msg += defender.append_accuracy(-1, attacker=attacker, move=self)
        if self.effect in (25, 259):
            msg += defender.append_evasion(-1, attacker=attacker, move=self)
        if self.effect in (69, 396):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_attack(-1, attacker=attacker, move=self)
        if self.effect in (70, 397, 435):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_defense(-1, attacker=attacker, move=self)
        if self.effect == 475:
            # This one has two different chance percents, one has to be hardcoded
            if random.randint(1, 100) <= 50:
                msg += defender.append_defense(-1, attacker=attacker, move=self)
        if self.effect in (21, 71, 357, 477):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_speed(-1, attacker=attacker, move=self)
        if self.effect == 72:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_spatk(-1, attacker=attacker, move=self)
        if self.effect == 73:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_spdef(-1, attacker=attacker, move=self)
        if self.effect == 74:
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_accuracy(-1, attacker=attacker, move=self)
        if self.effect == 183:
            msg += attacker.append_attack(-1, attacker=attacker, move=self)
        if self.effect in (183, 230, 309, 335, 405, 438, 442):
            msg += attacker.append_defense(-1, attacker=attacker, move=self)
        if self.effect == 480:
            msg += attacker.append_spatk(-1, attacker=attacker, move=self)
        if self.effect in (230, 309, 335):
            msg += attacker.append_spdef(-1, attacker=attacker, move=self)
        if self.effect in (219, 335):
            msg += attacker.append_speed(-1, attacker=attacker, move=self)
        # -2
        if self.effect in (59, 169):
            msg += defender.append_attack(-2, attacker=attacker, move=self)
        if self.effect in (60, 483):
            msg += defender.append_defense(-2, attacker=attacker, move=self)
        if self.effect == 61:
            msg += defender.append_speed(-2, attacker=attacker, move=self)
        if self.effect in (62, 169, 266):
            msg += defender.append_spatk(-2, attacker=attacker, move=self)
        if self.effect == 63:
            msg += defender.append_spdef(-2, attacker=attacker, move=self)
        if self.effect in (272, 297):
            if random.randint(1, 100) <= effect_chance:
                msg += defender.append_spdef(-2, attacker=attacker, move=self)
        if self.effect == 205:
            msg += attacker.append_spatk(-2, attacker=attacker, move=self)
        if self.effect == 479:
            msg += attacker.append_speed(-2, attacker=attacker, move=self)
        # other
        if self.effect == 26:
            attacker.attack_stage = 0
            attacker.defense_stage = 0
            attacker.spatk_stage = 0
            attacker.spdef_stage = 0
            attacker.speed_stage = 0
            attacker.accuracy_stage = 0
            attacker.evasion_stage = 0
            defender.attack_stage = 0
            defender.defense_stage = 0
            defender.spatk_stage = 0
            defender.spdef_stage = 0
            defender.speed_stage = 0
            defender.accuracy_stage = 0
            defender.evasion_stage = 0
            msg += "All pokemon had their stat stages reset!\n"
        if self.effect == 305:
            defender.attack_stage = 0
            defender.defense_stage = 0
            defender.spatk_stage = 0
            defender.spdef_stage = 0
            defender.speed_stage = 0
            defender.accuracy_stage = 0
            defender.evasion_stage = 0
            msg += f"{defender.name} had their stat stages reset!\n"
        if self.effect == 141:
            if random.randint(1, 100) <= effect_chance:
                msg += attacker.append_attack(1, attacker=attacker, move=self)
                msg += attacker.append_defense(1, attacker=attacker, move=self)
                msg += attacker.append_spatk(1, attacker=attacker, move=self)
                msg += attacker.append_spdef(1, attacker=attacker, move=self)
                msg += attacker.append_speed(1, attacker=attacker, move=self)
        if self.effect == 143:
            msg += attacker.damage(attacker.starting_hp // 2, battle)
            msg += attacker.append_attack(12, attacker=attacker, move=self)
        if self.effect == 317:
            amount = 1
            if battle.weather.get() in ("sun", "h-sun"):
                amount = 2
            msg += attacker.append_attack(amount, attacker=attacker, move=self)
            msg += attacker.append_spatk(amount, attacker=attacker, move=self)
        if self.effect == 364 and defender.nv.poison():
            msg += defender.append_attack(-1, attacker=attacker, move=self)
            msg += defender.append_spatk(-1, attacker=attacker, move=self)
            msg += defender.append_speed(-1, attacker=attacker, move=self)
        if self.effect == 329:
            msg += attacker.append_defense(3, attacker=attacker, move=self)
        if self.effect == 322:
            msg += attacker.append_spatk(3, attacker=attacker, move=self)
        if self.effect == 227:
            valid_stats = []
            if attacker.attack_stage < 6:
                valid_stats.append(attacker.append_attack)
            if attacker.defense_stage < 6:
                valid_stats.append(attacker.append_defense)
            if attacker.spatk_stage < 6:
                valid_stats.append(attacker.append_spatk)
            if attacker.spdef_stage < 6:
                valid_stats.append(attacker.append_spdef)
            if attacker.speed_stage < 6:
                valid_stats.append(attacker.append_speed)
            if attacker.evasion_stage < 6:
                valid_stats.append(attacker.append_evasion)
            if attacker.accuracy_stage < 6:
                valid_stats.append(attacker.append_accuracy)
            if valid_stats:
                stat_raise_func = random.choice(valid_stats)
                msg += stat_raise_func(2, attacker=attacker, move=self)
            else:
                msg += f"None of {attacker.name}'s stats can go any higher!\n"
        if self.effect == 473:
            raw_atk = attacker.get_raw_attack() + attacker.get_raw_spatk()
            raw_def = attacker.get_raw_defense() + attacker.get_raw_spdef()
            if raw_atk > raw_def:
                msg += attacker.append_attack(1, attacker=attacker, move=self)
                msg += attacker.append_spatk(1, attacker=attacker, move=self)
            else:
                msg += attacker.append_defense(1, attacker=attacker, move=self)
                msg += attacker.append_spdef(1, attacker=attacker, move=self)
        if self.effect == 485:
            msg += attacker.damage(attacker.starting_hp // 2, battle)
            msg += attacker.append_attack(2, attacker=attacker, move=self)
            msg += attacker.append_spatk(2, attacker=attacker, move=self)
            msg += attacker.append_speed(2, attacker=attacker, move=self)
        
        # Flinch
        if not defender.has_moved:
            for _ in range(numhits):
                if defender.flinched:
                    break
                if self.effect in (32, 76, 93, 147, 151, 159, 274, 275, 276, 425, 475, 501):
                    if random.randint(1, 100) <= effect_chance:
                        msg += defender.flinch(move=self, attacker=attacker)
                elif self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
                    if attacker.ability() == Ability.STENCH:
                        if random.randint(1, 100) <= 10:
                            msg += defender.flinch(move=self, attacker=attacker, source="its stench")
                    elif attacker.held_item == "kings-rock":
                        if random.randint(1, 100) <= 10:
                            msg += defender.flinch(move=self, attacker=attacker, source="its kings rock")
                    elif attacker.held_item == "razor-fang":
                        if random.randint(1, 100) <= 10:
                            msg += defender.flinch(move=self, attacker=attacker, source="its razor fang")
        
        # Move locking
        if self.effect == 87:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects its move from being disabled!\n"
            else:
                defender.disable.set(defender.last_move, random.randint(4, 7))
                msg += f"{defender.name}'s {defender.last_move.pretty_name} was disabled!\n"
        if self.effect == 176:
            if defender.ability(attacker=attacker, move=self) == Ability.OBLIVIOUS:
                msg += f"{defender.name} is too oblivious to be taunted!\n"
            elif defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being taunted!\n"
            else:
                if defender.has_moved:
                    defender.taunt.set_turns(4)
                else:
                    defender.taunt.set_turns(3)
                msg += f"{defender.name} is being taunted!\n"
        if self.effect == 91:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being encored!\n"
            else:
                defender.encore.set(defender.last_move, 4)
                if not defender.has_moved:
                    defender.owner.selected_action = defender.last_move
                msg += f"{defender.name} is giving an encore!\n"
        if self.effect == 166:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being tormented!\n"
            else:
                defender.torment = True
                msg += f"{defender.name} is tormented!\n"
        if self.effect == 193:
            attacker.imprison = True
            msg += f"{attacker.name} imprisons!\n"
        if self.effect == 237:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being heal blocked!\n"
            else:
                defender.heal_block.set_turns(5)
                msg += f"{defender.name} is blocked from healing!\n"
        if self.effect == 496:
            if defender.ability(attacker=attacker, move=self) == Ability.AROMA_VEIL:
                msg += f"{defender.name}'s aroma veil protects it from being heal blocked!\n"
            else:
                defender.heal_block.set_turns(2)
                msg += f"{defender.name} is blocked from healing!\n"
        
        # Weather changing
        if self.effect == 116:
            msg += battle.weather.set("sandstorm", attacker)
        if self.effect == 137:
            msg += battle.weather.set("rain", attacker)
        if self.effect == 138:
            msg += battle.weather.set("sun", attacker)
        if self.effect == 165:
            msg += battle.weather.set("hail", attacker)
        
        # Terrain changing
        if self.effect == 352:
            msg += battle.terrain.set("grassy", attacker)
        if self.effect == 353:
            msg += battle.terrain.set("misty", attacker)
        if self.effect == 369:
            msg += battle.terrain.set("electric", attacker)
        if self.effect == 395:
            msg += battle.terrain.set("psychic", attacker)
        
        # Protection
        if self.effect in (112, 117, 279, 356, 362, 384, 454, 488, 499):
            attacker.protection_used = True
            attacker.protection_chance *= 3
        if self.effect == 112:
            attacker.protect = True
            msg += f"{attacker.name} protected itself!\n"
        if self.effect == 117:
            attacker.endure = True
            msg += f"{attacker.name} braced itself!\n"
        if self.effect == 279:
            attacker.wide_guard = True
            msg += f"Wide guard protects {attacker.name}!\n"
        if self.effect == 350:
            attacker.crafty_shield = True
            msg += f"A crafty shield protects {attacker.name} from status moves!\n"
        if self.effect == 356:
            attacker.king_shield = True
            msg += f"{attacker.name} shields itself!\n"
        if self.effect == 362:
            attacker.spiky_shield = True
            msg += f"{attacker.name} shields itself!\n"
        if self.effect == 377:
            attacker.mat_block = True
            msg += f"{attacker.name} shields itself!\n"
        if self.effect == 384:
            attacker.baneful_bunker = True
            msg += f"{attacker.name} bunkers down!\n"
        if self.effect == 307:
            attacker.quick_guard = True
            msg += f"{attacker.name} guards itself!\n"
        if self.effect == 454:
            attacker.obstruct = True
            msg += f"{attacker.name} protected itself!\n"
        if self.effect == 488:
            attacker.silk_trap = True
            msg += f"{attacker.name} protected itself!\n"
        if self.effect == 499:
            attacker.burning_bulwark = True
            msg += f"{attacker.name} protected itself!\n"
        
        # Life orb
        if (
            attacker.held_item == "life-orb"
            and defender.owner.has_alive_pokemon()
            and self.damage_class != DamageClass.STATUS
            and (attacker.ability() != Ability.SHEER_FORCE or self.effect_chance is None)
            and self.effect != 149
        ):
            msg += attacker.damage(attacker.starting_hp // 10, battle, source="its life orb")
        
        # Swap outs
        # A poke is force-swapped out before activating red-card
        if self.effect in (29, 314):
            swaps = defender.owner.valid_swaps(attacker, battle, check_trap=False)
            if not swaps:
                pass
            elif defender.ability(attacker=attacker, move=self) == Ability.SUCTION_CUPS:
                msg += f"{defender.name}'s suction cups kept it in place!\n"
            elif defender.ability(attacker=attacker, move=self) == Ability.GUARD_DOG:
                msg += f"{defender.name}'s guard dog kept it in place!\n"
            elif defender.ingrain:
                msg += f"{defender.name} is ingrained in the ground!\n"
            else:
                msg += f"{defender.name} fled in fear!\n"
                msg += defender.remove(battle)
                idx = random.choice(swaps)
                defender.owner.switch_poke(idx, mid_turn=True)
                msg += defender.owner.current_pokemon.send_out(attacker, battle)
                # Safety in case the poke dies on send out.
                if defender.owner.current_pokemon is not None:
                    defender.owner.current_pokemon.has_moved = True
        # A red-card forces the attacker to swap to a random poke, even if they used a switch out move
        elif defender.held_item == "red-card" and defender.hp > 0 and self.damage_class != DamageClass.STATUS:
            swaps = attacker.owner.valid_swaps(defender, battle, check_trap=False)
            if not swaps:
                pass
            elif attacker.ability(attacker=defender, move=self) == Ability.SUCTION_CUPS:
                msg += f"{attacker.name}'s suction cups kept it in place from {defender.name}'s red card!\n"
                defender.held_item.use()
            elif attacker.ability(attacker=defender, move=self) == Ability.GUARD_DOG:
                msg += f"{attacker.name}'s guard dog kept it in place from {defender.name}'s red card!\n"
                defender.held_item.use()
            elif attacker.ingrain:
                msg += f"{attacker.name} is ingrained in the ground from {defender.name}'s red card!\n"
                defender.held_item.use()
            else:
                msg += f"{defender.name} held up its red card against {attacker.name}!\n"
                defender.held_item.use()
                msg += attacker.remove(battle)
                idx = random.choice(swaps)
                attacker.owner.switch_poke(idx, mid_turn=True)
                msg += attacker.owner.current_pokemon.send_out(defender, battle)
                # Safety in case the poke dies on send out.
                if attacker.owner.current_pokemon is not None:
                    attacker.owner.current_pokemon.has_moved = True
        elif self.effect in (128, 154, 229, 347):
            swaps = attacker.owner.valid_swaps(defender, battle, check_trap=False)
            if swaps:
                msg += f"{attacker.name} went back!\n"
                if self.effect == 128:
                    attacker.owner.baton_pass = BatonPass(attacker)
                msg += attacker.remove(battle)
                # Force this pokemon to immediately return to be attacked
                attacker.owner.mid_turn_remove = True
        
        # Trapping
        if self.effect in (107, 374, 385, 449, 452) and not defender.trapping:
            defender.trapping = True
            msg += f"{defender.name} can't escape!\n"
        if self.effect == 449 and not attacker.trapping:
            attacker.trapping = True
            msg += f"{attacker.name} can't escape!\n"
        
        # Attacker faints
        if self.effect in (169, 221, 271, 321):
            msg += attacker.faint(battle)
        
        # Struggle
        if self.effect == 255:
            msg += attacker.damage(attacker.starting_hp // 4, battle, attacker=attacker)
        
        # Pain Split
        if self.effect == 92:
            hp = (attacker.hp + defender.hp) // 2
            attacker.hp = min(attacker.starting_hp, hp)
            defender.hp = min(defender.starting_hp, hp)
            msg += "The battlers share their pain!\n"
        
        # Spite
        if self.effect == 101:
            defender.last_move.pp = max(0, defender.last_move.pp - 4)
            msg += f"{defender.name}'s {defender.last_move.pretty_name} was reduced!\n"
        
        # Eerie Spell
        if self.effect == 439 and defender.last_move is not None:
            defender.last_move.pp = max(0, defender.last_move.pp - 3)
            msg += f"{defender.name}'s {defender.last_move.pretty_name} was reduced!\n"
        
        # Heal Bell
        if self.effect == 103:
            for poke in attacker.owner.party:
                poke.nv.reset()
            msg += f"A bell chimed, and all of {attacker.owner.name}'s pokemon had status conditions removed!\n"
        
        # Psycho Shift
        if self.effect == 235:
            transfered_status = attacker.nv.current
            msg += defender.nv.apply_status(transfered_status, battle, attacker=attacker, move=self)
            if defender.nv.current == transfered_status:
                attacker.nv.reset()
                msg += f"{attacker.name}'s {transfered_status} was transfered to {defender.name}!\n"
            else:
                msg += "But it failed!\n"
        
        # Defog
        if self.effect == 259:
            defender.owner.spikes = 0
            defender.owner.toxic_spikes = 0
            defender.owner.stealth_rock = False
            defender.owner.sticky_web = False
            defender.owner.aurora_veil = ExpiringEffect(0)
            defender.owner.light_screen = ExpiringEffect(0)
            defender.owner.reflect = ExpiringEffect(0)
            defender.owner.mist = ExpiringEffect(0)
            defender.owner.safeguard = ExpiringEffect(0)
            attacker.owner.spikes = 0
            attacker.owner.toxic_spikes = 0
            attacker.owner.stealth_rock = False
            attacker.owner.sticky_web = False
            battle.terrain.end()
            msg += f"{attacker.name} blew away the fog!\n"
        
        # Trick room
        if self.effect == 260:
            if battle.trick_room.active():
                battle.trick_room.set_turns(0)
                msg += "The Dimensions returned back to normal!\n"
            else:
                battle.trick_room.set_turns(5)
                msg += f"{attacker.name} twisted the dimensions!\n"
        
        # Magic Room
        if self.effect == 287:
            if battle.magic_room.active():
                battle.magic_room.set_turns(0)
                msg += "The room returns to normal, and held items regain their effect!\n"
            else:
                battle.magic_room.set_turns(5)
                msg += "A bizzare area was created, and pokemon's held items lost their effect!\n"
        
        # Wonder Room
        if self.effect == 282:
            if battle.wonder_room.active():
                battle.wonder_room.set_turns(0)
                msg += "The room returns to normal, and stats swap back to what they were before!\n"
            else:
                battle.wonder_room.set_turns(5)
                msg += "A bizzare area was created, and pokemon's defense and special defense were swapped!\n"
        
        # Perish Song
        if self.effect == 115:
            msg += "All pokemon hearing the song will faint after 3 turns!\n"
            if attacker.perish_song.active():
                msg += f"{attacker.name} is already under the effect of perish song!\n"
            else:
                attacker.perish_song.set_turns(4)
            if defender.perish_song.active():
                msg += f"{defender.name} is already under the effect of perish song!\n"
            elif defender.ability(attacker=attacker, move=self) == Ability.SOUNDPROOF:
                msg += f"{defender.name}'s soundproof protects it from hearing the song!\n"
            else:
                defender.perish_song.set_turns(4)
            
        # Nightmare
        if self.effect == 108:
            defender.nightmare = True
            msg += f"{defender.name} fell into a nightmare!\n"
        
        # Gravity
        if self.effect == 216:
            battle.gravity.set_turns(5)
            msg += "Gravity intensified!\n"
            defender.telekinesis.set_turns(0)
            if defender.fly:
                defender.fly = False
                defender.locked_move = None
                msg += f"{defender.name} fell from the sky!\n"
        
        # Spikes
        if self.effect == 113:
            defender.owner.spikes += 1
            msg += f"Spikes were scattered around the feet of {defender.owner.name}'s team!\n"
        
        # Toxic Spikes
        if self.effect == 250:
            defender.owner.toxic_spikes += 1
            msg += f"Toxic spikes were scattered around the feet of {defender.owner.name}'s team!\n"
        
        # Stealth Rock
        if self.effect == 267:
            defender.owner.stealth_rock = True
            msg += f"Pointed stones float in the air around {defender.owner.name}'s team!\n"
        
        # Sticky Web
        if self.effect == 341:
            defender.owner.sticky_web = True
            msg += f"A sticky web is shot around the feet of {defender.owner.name}'s team!\n"
        
        # Defense curl
        if self.effect == 157 and not attacker.defense_curl:
            attacker.defense_curl = True
        
        # Psych Up
        if self.effect == 144:
            attacker.attack_stage = defender.attack_stage
            attacker.defense_stage = defender.defense_stage
            attacker.spatk_stage = defender.spatk_stage
            attacker.spdef_stage = defender.spdef_stage
            attacker.speed_stage = defender.speed_stage
            attacker.accuracy_stage = defender.accuracy_stage
            attacker.evasion_stage = defender.evasion_stage
            attacker.focus_energy = defender.focus_energy
            msg += "It psyched itself up!\n"
        
        # Conversion
        if self.effect == 31:
            t = attacker.moves[0].type
            if t not in ElementType.__members__.values():
                t = ElementType.NORMAL
            attacker.type_ids = [t]
            t = ElementType(t).name.lower()
            msg += f"{attacker.name} transformed into a {t} type!\n"
        
        # Conversion 2
        if self.effect == 94:
            t = self.get_conversion_2(attacker, defender, battle)
            attacker.type_ids = [t]
            t = ElementType(t).name.lower()
            msg += f"{attacker.name} transformed into a {t} type!\n"
        
        # Burn up
        if self.effect == 398:
            attacker.type_ids.remove(ElementType.FIRE)
            msg += f"{attacker.name} lost its fire type!\n"

        # Double shock
        if self.effect == 481:
            attacker.type_ids.remove(ElementType.ELECTRIC)
            msg += f"{attacker.name} lost its electric type!\n"
        
        # Forest's Curse
        if self.effect == 376:
            defender.type_ids.append(ElementType.GRASS)
            msg += f"{defender.name} added grass type!\n"
        
        # Trick or Treat
        if self.effect == 343:
            defender.type_ids.append(ElementType.GHOST)
            msg += f"{defender.name} added ghost type!\n"
        
        # Soak
        if self.effect == 295:
            defender.type_ids = [ElementType.WATER]
            msg += f"{defender.name} was transformed into a water type!\n"
        
        # Magic Powder
        if self.effect == 456:
            defender.type_ids = [ElementType.PSYCHIC]
            msg += f"{defender.name} was transformed into a psychic type!\n"
        
        # Camouflage
        if self.effect == 214:
            if battle.terrain.item == "grassy":
                attacker.type_ids = [ElementType.GRASS]
                msg += f"{attacker.name} was transformed into a grass type!\n"
            elif battle.terrain.item == "misty":
                attacker.type_ids = [ElementType.FAIRY]
                msg += f"{attacker.name} was transformed into a fairy type!\n"
            elif battle.terrain.item == "electric":
                attacker.type_ids = [ElementType.ELECTRIC]
                msg += f"{attacker.name} was transformed into a electric type!\n"
            elif battle.terrain.item == "psychic":
                attacker.type_ids = [ElementType.PSYCHIC]
                msg += f"{attacker.name} was transformed into a psychic type!\n"
            else:
                attacker.type_ids = [ElementType.NORMAL]
                msg += f"{attacker.name} was transformed into a normal type!\n"
        
        # Role Play
        if self.effect == 179:
            attacker.ability_id = defender.ability_id
            ability_name = Ability(attacker.ability_id).pretty_name
            msg += f"{attacker.name} acquired {ability_name}!\n"
            msg += attacker.send_out_ability(defender, battle)
        
        # Simple Beam
        if self.effect == 299:
            defender.ability_id = Ability.SIMPLE
            msg += f"{defender.name} acquired simple!\n"
            msg += defender.send_out_ability(attacker, battle)
        
        # Entrainment
        if self.effect == 300:
            defender.ability_id = attacker.ability_id
            ability_name = Ability(defender.ability_id).pretty_name
            msg += f"{defender.name} acquired {ability_name}!\n"
            msg += defender.send_out_ability(attacker, battle)
        
        # Worry Seed
        if self.effect == 248:
            defender.ability_id = Ability.INSOMNIA
            if defender.nv.sleep():
                defender.nv.reset()
            msg += f"{defender.name} acquired insomnia!\n"
            msg += defender.send_out_ability(attacker, battle)
        
        # Skill Swap
        if self.effect == 192:
            defender.ability_id, attacker.ability_id = attacker.ability_id, defender.ability_id
            ability_name = Ability(defender.ability_id).pretty_name
            msg += f"{defender.name} acquired {ability_name}!\n"
            msg += defender.send_out_ability(attacker, battle)
            ability_name = Ability(attacker.ability_id).pretty_name
            msg += f"{attacker.name} acquired {ability_name}!\n"
            msg += attacker.send_out_ability(defender, battle)
        
        # Aurora Veil
        if self.effect == 407:
            if attacker.held_item == "light-clay":
                attacker.owner.aurora_veil.set_turns(8)
            else:
                attacker.owner.aurora_veil.set_turns(5)
            msg += f"{attacker.name} put up its aurora veil!\n"
        
        # Light Screen
        if self.effect in (36, 421):
            if attacker.held_item == "light-clay":
                attacker.owner.light_screen.set_turns(8)
            else:
                attacker.owner.light_screen.set_turns(5)
            msg += f"{attacker.name} put up its light screen!\n"
        
        # Reflect
        if self.effect in (66, 422):
            if attacker.held_item == "light-clay":
                attacker.owner.reflect.set_turns(8)
            else:
                attacker.owner.reflect.set_turns(5)
            msg += f"{attacker.name} put up its reflect!\n"
        
        # Mist
        if self.effect == 47:
            attacker.owner.mist.set_turns(5)
            msg += f"{attacker.name} gained the protection of mist!\n"
        
        # Bind
        if self.effect in (43, 262) and not defender.substitute and not defender.bind.active():
            if attacker.held_item == "grip-claw":
                defender.bind.set_turns(7)
            else:
                defender.bind.set_turns(random.randint(4, 5))
            msg += f"{defender.name} was squeezed!\n"
        
        # Sketch
        if self.effect == 96:
            m = defender.last_move.copy()
            attacker.moves[attacker.moves.index(self)] = m
            msg += f"The move {m.pretty_name} was sketched!\n"
            
        # Transform
        if self.effect == 58:
            msg += f"{attacker.name} transformed into {defender._name}!\n"
            attacker.transform(defender)
        
        # Substitute
        if self.effect == 80:
            hp = attacker.starting_hp // 4
            msg += attacker.damage(hp, battle, attacker=attacker, source="building a substitute")
            attacker.substitute = hp
            attacker.bind = ExpiringEffect(0)
            msg += f"{attacker.name} made a substitute!\n"
        
        # Shed Tail
        if self.effect == 493:
            hp = attacker.starting_hp // 4
            msg += attacker.damage(attacker.starting_hp // 2, battle, attacker=attacker, source="building a substitute")
            attacker.owner.next_substitute = hp
            attacker.bind = ExpiringEffect(0)
            msg += f"{attacker.name} left behind a substitute!\n"
            msg += attacker.remove(battle)
            # Force this pokemon to immediately return to be attacked
            attacker.owner.mid_turn_remove = True
        
        # Throat Chop
        if self.effect == 393 and not defender.silenced.active():
            if random.randint(1, 100) <= effect_chance:
                defender.silenced.set_turns(3)
                msg += f"{defender.name} was silenced!\n"
        
        # Speed Swap
        if self.effect == 399:
            attacker.speed, defender.speed = defender.speed, attacker.speed
            msg += "Both pokemon exchange speed!\n"
        
        # Mimic
        if self.effect == 83:
            m = defender.last_move.copy()
            m.pp = m.starting_pp
            attacker.moves[attacker.moves.index(self)] = m
            msg += f"{attacker.name} mimicked {m.pretty_name}!\n"
        
        # Rage
        if self.effect == 82:
            attacker.rage = True
            msg += f"{attacker.name}'s rage is building!\n"
            
        # Mind Reader
        if self.effect == 95:
            defender.mind_reader.set(attacker, 2)
            msg += f"{attacker.name} took aim at {defender.name}!\n"
        
        # Destiny Bond
        if self.effect == 99:
            attacker.destiny_bond = True
            attacker.destiny_bond_cooldown.set_turns(2)
            msg += f"{attacker.name} is trying to take its foe with it!\n"
        
        # Ingrain
        if self.effect == 182:
            attacker.ingrain = True
            msg += f"{attacker.name} planted its roots!\n"
        
        # Attract
        if self.effect == 121:
            msg += defender.infatuate(attacker, move=self)
        
        # Heart Swap
        if self.effect == 251:
            attacker.attack_stage, defender.attack_stage = defender.attack_stage, attacker.attack_stage
            attacker.defense_stage, defender.defense_stage = defender.defense_stage, attacker.defense_stage
            attacker.spatk_stage, defender.spatk_stage = defender.spatk_stage, attacker.spatk_stage
            attacker.spdef_stage, defender.spdef_stage = defender.spdef_stage, attacker.spdef_stage
            attacker.speed_stage, defender.speed_stage = defender.speed_stage, attacker.speed_stage
            attacker.accuracy_stage, defender.accuracy_stage = defender.accuracy_stage, attacker.accuracy_stage
            attacker.evasion_stage, defender.evasion_stage = defender.evasion_stage, attacker.evasion_stage
            msg += f"{attacker.name} switched stat changes with {defender.name}!\n"
        
        # Power Swap
        if self.effect == 244:
            attacker.attack_stage, defender.attack_stage = defender.attack_stage, attacker.attack_stage
            attacker.spatk_stage, defender.spatk_stage = defender.spatk_stage, attacker.spatk_stage
            msg += f"{attacker.name} switched attack and special attack stat changes with {defender.name}!\n"
        
        # Guard Swap
        if self.effect == 245:
            attacker.defense_stage, defender.defense_stage = defender.defense_stage, attacker.defense_stage
            attacker.spdef_stage, defender.spdef_stage = defender.spdef_stage, attacker.spdef_stage
            msg += f"{attacker.name} switched defense and special defense stat changes with {defender.name}!\n"
        
        # Aqua Ring
        if self.effect == 252:
            attacker.aqua_ring = True
            msg += f"{attacker.name} surrounded itself with a veil of water!\n"
        
        # Magnet Rise
        if self.effect == 253:
            attacker.magnet_rise.set_turns(5)
            msg += f"{attacker.name} levitated with electromagnetism!\n"
        
        # Healing Wish
        if self.effect == 221:
            attacker.owner.healing_wish = True
            msg += f"{attacker.name}'s replacement will be restored!\n"
        
        # Lunar Dance
        if self.effect == 271:
            attacker.owner.lunar_dance = True
            msg += f"{attacker.name}'s replacement will be restored!\n"

        # Gastro Acid
        if self.effect == 240:
            defender.ability_id = None
            msg += f"{defender.name}'s ability was disabled!\n"
        
        # Lucky Chant
        if self.effect == 241:
            attacker.lucky_chant.set_turns(5)
            msg += f"{attacker.name} is shielded from critical hits!\n"
        
        # Safeguard
        if self.effect == 125:
            attacker.owner.safeguard.set_turns(5)
            msg += f"{attacker.name} is protected from status effects!\n"
        
        # Guard Split
        if self.effect == 280:
            attacker.defense_split = defender.get_raw_defense()
            attacker.spdef_split = defender.get_raw_spdef()
            defender.defense_split = attacker.get_raw_defense()
            defender.spdef_split = attacker.get_raw_spdef()
            msg += f"{attacker.name} and {defender.name} shared their guard!\n"
        
        # Power Split
        if self.effect == 281:
            attacker.attack_split = defender.get_raw_attack()
            attacker.spatk_split = defender.get_raw_spatk()
            defender.attack_split = attacker.get_raw_attack()
            defender.spatk_split = attacker.get_raw_spatk()
            msg += f"{attacker.name} and {defender.name} shared their power!\n"
        
        # Smack Down/Thousand Arrows
        if self.effect in (288, 373):
            defender.telekinesis.set_turns(0)
            if defender.fly:
                defender.fly = False
                defender.locked_move = None
                defender.has_moved = True
                msg += f"{defender.name} was shot out of the air!\n"
            if not defender.grounded(battle, attacker=attacker, move=self):
                defender.grounded_by_move = True
                msg += f"{defender.name} was grounded!\n"
        
        # Reflect Type
        if self.effect == 319:
            attacker.type_ids = defender.type_ids.copy()
            msg += f"{attacker.name}'s type changed to match {defender.name}!\n"
        
        # Charge
        if self.effect == 175:
            # TODO: Gen 9 makes charge last until an electric move is used
            attacker.charge.set_turns(2)
            msg += f"{attacker.name} charges up electric type moves!\n"
        
        # Magic Coat
        if self.effect == 184:
            attacker.magic_coat = True
            msg += f"{attacker.name} shrouded itself with a magic coat!\n"
        
        # Tailwind
        if self.effect == 226:
            attacker.owner.tailwind.set_turns(4)
            msg += f"{attacker.owner.name}'s team gets a tailwind!\n"
            if attacker.ability() == Ability.WIND_RIDER:
                msg += attacker.append_attack(1, attacker=attacker, source="its wind rider")
        
        # Fling
        if self.effect == 234 and attacker.held_item.can_remove():
            item = attacker.held_item.name
            msg += f"{attacker.name}'s {item} was flung away!\n"
            if attacker.held_item.is_berry():
                msg += attacker.held_item.eat_berry(consumer=defender, attacker=attacker, move=self)
            else:
                attacker.held_item.use()
                if item == "flame-orb":
                    msg += defender.nv.apply_status("burn", battle, attacker=attacker, move=self)
                elif item in ("kings-rock", "razor-fang"):
                    msg += defender.flinch(attacker=attacker, move=self)
                elif item == "light-ball":
                    msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
                elif item == "mental-herb":
                    defender.infatuated = None
                    defender.taunt = ExpiringEffect(0)
                    defender.encore = ExpiringItem()
                    defender.torment = False
                    defender.disable = ExpiringItem()
                    defender.heal_block = ExpiringEffect(0)
                    msg += f"{defender.name} feels refreshed!\n"
                elif item == "poison-barb":
                    msg += defender.nv.apply_status("poison", battle, attacker=attacker, move=self)
                elif item == "toxic-orb":
                    msg += defender.nv.apply_status("b-poison", battle, attacker=attacker, move=self)
                elif item == "white-herb":
                    defender.attack_stage = max(0, defender.attack_stage)
                    defender.defense_stage = max(0, defender.defense_stage)
                    defender.spatk_stage = max(0, defender.spatk_stage)
                    defender.spdef_stage = max(0, defender.spdef_stage)
                    defender.speed_stage = max(0, defender.speed_stage)
                    defender.accuracy_stage = max(0, defender.accuracy_stage)
                    defender.evasion_stage = max(0, defender.evasion_stage)
                    msg += f"{defender.name} feels refreshed!\n"
        
        # Thief
        if self.effect == 106 and defender.held_item.has_item() and defender.held_item.can_remove() and not defender.substitute and not attacker.held_item.has_item():
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                defender.held_item.transfer(attacker.held_item)
                msg += f"{defender.name}'s {attacker.held_item.name} was stolen!\n"
        
        # Trick
        if self.effect == 178:
            attacker.held_item.swap(defender.held_item)
            msg += f"{attacker.name} and {defender.name} swapped their items!\n"
            if attacker.held_item.name is not None:
                msg += f"{attacker.name} gained {attacker.held_item.name}!\n"
            if defender.held_item.name is not None:
                msg += f"{defender.name} gained {defender.held_item.name}!\n"
        
        # Knock off
        if self.effect == 189 and defender.held_item.has_item() and defender.held_item.can_remove() and not defender.substitute and attacker.hp > 0:
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                msg += f"{defender.name} lost its {defender.held_item.name}!\n"
                defender.held_item.remove()
        
        # Teatime
        if self.effect == 476:
            msgadd = ""
            for poke in (attacker, defender):
                msgadd += poke.held_item.eat_berry(attacker=attacker, move=self)
            msg += msgadd
            if not msgadd:
                msg += "But nothing happened..."
        
        # Corrosive Gas
        if self.effect == 430:
            if defender.ability(attacker=attacker, move=self) == Ability.STICKY_HOLD:
                msg += f"{defender.name}'s sticky hand kept hold of its item!\n"
            else:
                msg += f"{defender.name}'s {defender.held_item.name} was corroded!\n"
                defender.corrosive_gas = True
        
        # Mud Sport
        if self.effect == 202:
            attacker.owner.mud_sport.set_turns(6)
            msg += "Electricity's power was weakened!\n"
        
        # Water Sport
        if self.effect == 211:
            attacker.owner.water_sport.set_turns(6)
            msg += "Fire's power was weakened!\n"
        
        # Power Trick
        if self.effect == 239:
            attacker.power_trick = not attacker.power_trick
            msg += f"{attacker.name} switched its Attack and Defense!\n"
        
        # Power Shift
        if self.effect == 466:
            attacker.power_shift = not attacker.power_shift
            msg += f"{attacker.name} switched its offensive and defensive stats!\n"
        
        # Yank
        if self.effect == 188:
            if battle.terrain.item == "electric" and defender.grounded(battle, attacker=attacker, move=self):
                msg += f"{defender.name} keeps alert from being shocked by the electric terrain!\n"
            else:
                defender.yawn.set_turns(2)
                msg += f"{defender.name} is drowsy!\n"
        
        # Rototiller
        if self.effect == 340:
            for p in (attacker, defender):
                if ElementType.GRASS not in p.type_ids:
                    continue
                if not p.grounded(battle):
                    continue
                if p.dive or p.dig or p.fly or p.shadow_force:
                    continue
                msg += p.append_attack(1, attacker=attacker, move=self)
                msg += p.append_spatk(1, attacker=attacker, move=self)
        
        # Flower Shield
        if self.effect == 351:
            for p in (attacker, defender):
                if ElementType.GRASS not in p.type_ids:
                    continue
                if not p.grounded(battle):
                    continue
                if p.dive or p.dig or p.fly or p.shadow_force:
                    continue
                msg += p.append_defense(1, attacker=attacker, move=self)
        
        # Ion Deluge
        if self.effect == 345:
            attacker.ion_deluge = True
            msg += f"{attacker.name} charges up the air!\n"
        
        # Topsy Turvy
        if self.effect == 348:
            defender.attack_stage = -defender.attack_stage
            defender.defense_stage = -defender.defense_stage
            defender.spatk_stage = -defender.spatk_stage
            defender.spdef_stage = -defender.spdef_stage
            defender.speed_stage = -defender.speed_stage
            defender.accuracy_stage = -defender.accuracy_stage
            defender.evasion_stage = -defender.evasion_stage
            msg += f"{defender.name}'s stat stages were inverted!\n"

        # Electrify
        if self.effect == 354:
            defender.electrify = True
            msg += f"{defender.name}'s move was charged with electricity!\n"
        
        # Instruct
        if self.effect == 403:
            hm = defender.has_moved
            defender.has_moved = False
            msg += defender.last_move.use(defender, attacker, battle)
            defender.has_moved = hm
        
        # Core Enforcer
        if self.effect == 402 and defender.has_moved and defender.ability_changeable():
            defender.ability_id = None
            msg += f"{defender.name}'s ability was nullified!\n"

        # Laser Focus
        if self.effect == 391:
            attacker.laser_focus.set_turns(2)
            msg += f"{attacker.name} focuses!\n"

        # Powder
        if self.effect == 378:
            defender.powdered = True
            msg += f"{defender.name} was coated in powder!\n"

        # Rapid/Mortal Spin
        if self.effect in (130, 486):
            attacker.bind.set_turns(0)
            attacker.trapping = False
            attacker.leech_seed = False
            attacker.owner.spikes = 0
            attacker.owner.toxic_spikes = 0
            attacker.owner.stealth_rock = False
            attacker.owner.sticky_web = False
            msg += f"{attacker.name} was released!\n"

        # Snatch
        if self.effect == 196:
            attacker.snatching = True
            msg += f"{attacker.name} waits for a target to make a move!\n"

        # Telekinesis
        if self.effect == 286:
            defender.telekinesis.set_turns(5)
            msg += f"{defender.name} was hurled into the air!\n"

        # Embargo
        if self.effect == 233:
            defender.embargo.set_turns(6)
            msg += f"{defender.name} can't use items anymore!\n"
            
        # Echoed Voice
        if self.effect == 303:
            attacker.echoed_voice_power = min(attacker.echoed_voice_power + 40, 200)
            attacker.echoed_voice_used = True
            msg += f"{attacker.name}'s voice echos!\n"

        # Bestow
        if self.effect == 324:
            attacker.held_item.transfer(defender.held_item)
            msg += f"{attacker.name} gave its {defender.held_item.name} to {defender.name}!\n"

        # Curse
        if self.effect == 110:
            if ElementType.GHOST in attacker.type_ids:
                msg += attacker.damage(attacker.starting_hp // 2, battle, source="inflicting the curse")
                defender.curse = True
                msg += f"{defender.name} was cursed!\n"
            else:
                msg += attacker.append_speed(-1, attacker=attacker, move=self)
                msg += attacker.append_attack(1, attacker=attacker, move=self)
                msg += attacker.append_defense(1, attacker=attacker, move=self)

        # Autotomize
        if self.effect == 285:
            attacker.autotomize += 1
            msg += f"{attacker.name} became nimble!\n"

        # Fell Stinger
        if self.effect == 342 and defender.hp == 0:
            msg += attacker.append_attack(3, attacker=attacker, move=self)
        
        # Fairy Lock
        if self.effect == 355:
            attacker.fairy_lock.set_turns(2)
            msg += f"{attacker.name} prevents escape next turn!\n"

        # Grudge
        if self.effect == 195:
            attacker.grudge = True
            msg += f"{attacker.name} has a grudge!\n"

        # Foresight
        if self.effect == 114:
            defender.foresight = True
            msg += f"{attacker.name} identified {defender.name}!\n"
        
        # Miracle Eye
        if self.effect == 217:
            defender.miracle_eye = True
            msg += f"{attacker.name} identified {defender.name}!\n"

        # Clangorous Soul
        if self.effect == 414:
            msg += attacker.damage(attacker.starting_hp // 3, battle)

        # No Retreat
        if self.effect == 427:
            attacker.no_retreat = True
            msg += f"{attacker.name} takes its last stand!\n"

        # Recycle
        if self.effect == 185:
            attacker.held_item.recover(attacker.held_item)
            msg += f"{attacker.name} recovered their {attacker.held_item.name}!\n"
            if attacker.held_item.should_eat_berry(defender):
                msg += attacker.held_item.eat_berry(attacker=defender, move=self)
        
        # Court Change
        if self.effect == 431:
            attacker.owner.spikes, defender.owner.spikes = defender.owner.spikes, attacker.owner.spikes
            attacker.owner.toxic_spikes, defender.owner.toxic_spikes = defender.owner.toxic_spikes, attacker.owner.toxic_spikes
            attacker.owner.stealth_rock, defender.owner.stealth_rock = defender.owner.stealth_rock, attacker.owner.stealth_rock
            attacker.owner.sticky_web, defender.owner.sticky_web = defender.owner.sticky_web, attacker.owner.sticky_web
            attacker.owner.aurora_veil, defender.owner.aurora_veil = defender.owner.aurora_veil, attacker.owner.aurora_veil
            attacker.owner.light_screen, defender.owner.light_screen = defender.owner.light_screen, attacker.owner.light_screen
            attacker.owner.reflect, defender.owner.reflect = defender.owner.reflect, attacker.owner.reflect
            attacker.owner.mist, defender.owner.mist = defender.owner.mist, attacker.owner.mist
            attacker.owner.safeguard, defender.owner.safeguard = defender.owner.safeguard, attacker.owner.safeguard
            attacker.owner.tailwind, defender.owner.tailwind = defender.owner.tailwind, attacker.owner.tailwind
            msg += "Active battle effects swapped sides!\n"
        
        # Roost
        if self.effect == 215:
            attacker.roost = True
            if ElementType.FLYING in attacker.type_ids:
                msg += f"{attacker.name}'s flying type is surpressed!\n"
        
        # Pluck
        if self.effect == 225 and defender.ability(attacker=attacker, move=self) != Ability.STICKY_HOLD:
            msg += defender.held_item.eat_berry(consumer=attacker)
        
        # Focus energy
        if self.effect == 48:
            attacker.focus_energy = True
            msg += f"{attacker.name} focuses on its target!\n"

        # Natural Gift
        if self.effect == 223:
            msg += f"{attacker.name}'s {attacker.held_item.name} was consumed!\n"
            attacker.held_item.use()

        # Gulp Missile
        if self.effect == 258 and attacker.ability() == Ability.GULP_MISSILE and attacker._name == "Cramorant":
            if attacker.hp > attacker.starting_hp // 2:
                if attacker.form("Cramorant-gulping"):
                    msg += f"{attacker.name} gulped up an arrokuda!\n"
            else:
                if attacker.form("Cramorant-gorging"):
                    msg += f"{attacker.name} gulped up a pikachu!\n"
        
        # Steel Roller
        if self.effect in (418, 448) and battle.terrain.item is not None:
            battle.terrain.end()
            msg += "The terrain was cleared!\n"
        
        # Octolock
        if self.effect == 452:
            defender.octolock = True
            msg += f"{defender.name} is octolocked!\n"
        
        # Stuff Cheeks
        if self.effect == 453:
            msg += attacker.held_item.eat_berry()
        
        # Plasma Fists
        if self.effect == 455:
            if not battle.plasma_fists:
                battle.plasma_fists = True
                msg += f"{attacker.name} electrifies the battlefield, energizing normal type moves!\n"
        
        # Secret Power
        if self.effect == 198:
            if random.randint(1, 100) <= effect_chance:
                if battle.terrain.item == "grassy":
                    msg += defender.nv.apply_status("sleep", battle, attacker=attacker, move=self)
                elif battle.terrain.item == "misty":
                    msg += defender.append_spatk(-1, attacker=attacker, move=self)
                elif battle.terrain.item == "psychic":
                    msg += defender.append_speed(-1, attacker=attacker, move=self)
                else:
                    msg += defender.nv.apply_status("paralysis", battle, attacker=attacker, move=self)
        
        if self.is_sound_based() and attacker.held_item == "throat-spray":
            msg += attacker.append_spatk(1, attacker=attacker, source="it's throat spray")
            attacker.held_item.use()
        
        # Tar Shot
        if self.effect == 477 and not defender.tar_shot:
            defender.tar_shot = True
            msg += f"{defender.name} is covered in sticky tar!\n"
        
        # Tidy Up
        if self.effect == 487:
            defender.owner.spikes = 0
            defender.owner.toxic_spikes = 0
            defender.owner.stealth_rock = False
            defender.owner.sticky_web = False
            defender.substitute = 0
            attacker.owner.spikes = 0
            attacker.owner.toxic_spikes = 0
            attacker.owner.stealth_rock = False
            attacker.owner.sticky_web = False
            attacker.substitute = 0
            msg += f"{attacker.name} tidied up!\n"
        
        # Syrup Bomb
        if self.effect == 503:
            defender.syrup_bomb.set_turns(4)
            msg += f"{defender.name} got covered in sticky candy syrup!\n"
        
        # Dancer Ability - Runs at the end of move usage
        if defender.ability(attacker=attacker, move=self) == Ability.DANCER and self.is_dance() and use_pp:
            hm = defender.has_moved
            msg += self.use(defender, attacker, battle, use_pp=False)
            defender.has_moved = hm
        
        return msg