import random
from ..misc import LockedMove, BatonPass, ExpiringEffect, ExpiringItem
from ..enums import Ability


class MoveUse:
    """Main move execution logic."""

    def use(self, attacker, defender, battle, *, use_pp=True, override_sleep=False, bounced=False):
        """Uses this move as attacker on defender."""
        if attacker.has_moved and use_pp:
            return ""
        self.used = True
        if use_pp:
            attacker.has_moved = True
            attacker.last_move = self
            attacker.beak_blast = False
            attacker.destiny_bond = False
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

        if attacker.locked_move is None and use_pp:
            self.pp -= 1
            if defender.ability(attacker=attacker, move=self) == Ability.PRESSURE and self.pp != 0:
                if self.targets_opponent() or self.effect in (113, 193, 196, 250, 267):
                    self.pp -= 1
            if self.pp == 0:
                msg += "It ran out of PP!\n"

        if attacker.choice_move is None and use_pp:
            if attacker.held_item in ("choice-scarf", "choice-band", "choice-specs"):
                attacker.choice_move = self
            elif attacker.ability() == Ability.GORILLA_TACTICS:
                attacker.choice_move = self

        if attacker.ability() == Ability.STANCE_CHANGE:
            from ..enums import DamageClass
            if attacker._name == "Aegislash" and self.damage_class in (DamageClass.PHYSICAL, DamageClass.SPECIAL):
                if attacker.form("Aegislash-blade"):
                    msg += f"{attacker.name} draws its blade!\n"
            if attacker._name == "Aegislash-blade" and self.effect == 356:
                if attacker.form("Aegislash"):
                    msg += f"{attacker.name} readies its shield!\n"

        if attacker.powdered and current_type == ElementType.FIRE and battle.weather.get() != "h-rain":
            msg += attacker.damage(attacker.starting_hp // 4, battle, source="its powder exploding")
            return msg

        if defender.snatching and self.selectable_by_snatch():
            msg += f"{defender.name} snatched the move!\n"
            msg += self.use(defender, attacker, battle, use_pp=False)
            return msg

        if not self.check_executable(attacker, defender, battle):
            msg += "But it failed!\n"
            if self.effect in (28, 118):
                attacker.locked_move = None
            attacker.last_move_failed = True
            return msg

        if attacker.locked_move is None:
            if self.effect == 152 and battle.weather.get() not in ("sun", "h-sun"):
                attacker.locked_move = LockedMove(self, 2)
            if self.effect == 502:
                if battle.weather.get() not in ("rain", "h-rain"):
                    attacker.locked_move = LockedMove(self, 2)
                else:
                    msg += attacker.append_spatk(1, attacker=attacker, move=self)
            if self.effect in (40, 76, 81, 146, 156, 256, 257, 264, 273, 332, 333, 366, 451):
                attacker.locked_move = LockedMove(self, 2)
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
            if self.effect == 118:
                attacker.locked_move = LockedMove(self, 5)
            if self.effect == 28:
                attacker.locked_move = LockedMove(self, random.randint(2, 3))
            if self.effect == 160:
                attacker.locked_move = LockedMove(self, random.randint(2, 5))
            if self.effect == 256:
                attacker.dive = True
            if self.effect == 257:
                attacker.dig = True
            if self.effect in (156, 264):
                attacker.fly = True
            if self.effect == 273:
                attacker.shadow_force = True

        if self.effect == 81 and attacker.locked_move:
            if attacker.locked_move.turn != 0:
                msg += "It's recharging!\n"
                return msg

        elif self.effect in (40, 76, 146, 152, 156, 256, 257, 264, 273, 332, 333, 366, 451, 502) and attacker.locked_move:
            if attacker.locked_move.turn != 1:
                if self.effect == 146:
                    msg += attacker.append_defense(1, attacker=attacker, move=self)
                elif self.effect in (451, 502):
                    msg += attacker.append_spatk(1, attacker=attacker, move=self)
                else:
                    msg += "It's charging up!\n"
                    if self.effect == 256 and attacker.ability() == Ability.GULP_MISSILE and attacker._name == "Cramorant":
                        if attacker.hp > attacker.starting_hp // 2:
                            if attacker.form("Cramorant-gulping"):
                                msg += f"{attacker.name} gulped up an arrokuda!\n"
                        else:
                            if attacker.form("Cramorant-gorging"):
                                msg += f"{attacker.name} gulped up a pikachu!\n"
                return msg

        elif self.effect == 27:
            if attacker.locked_move.turn != 2:
                msg += "It's storing energy!\n"
                return msg

        elif self.effect in (118, 160) and attacker.locked_move:
            if attacker.locked_move.turn != attacker.locked_move._remaining_turns:
                return msg

        msg += self.check_semi_invulnerable(attacker, defender, battle)
        if msg:
            return msg
        msg += self.check_protect(attacker, defender, battle)
        if msg:
            return msg
        msg += self.check_hit(attacker, defender, battle)
        if msg:
            return msg

        if self.target in (MoveTarget.ALL_OPPONENTS, MoveTarget.ALL_OTHER_POKEMON, MoveTarget.ALL_POKEMON):
            pass
        else:
            msg += self.check_effective(attacker, defender, battle, current_type)
            if not msg:
                msg = "But it had no effect!\n"
            else:
                msg += self.attack(attacker, defender, battle)

        return msg