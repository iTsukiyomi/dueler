import random
from .expiring_effect import ExpiringEffect
from ..enums import Ability, ElementType


class NonVolatileEffect():

    def __init__(self, pokemon):
        self.current = ""
        self.pokemon = pokemon
        self.sleep_timer = ExpiringEffect(0)
        self.badly_poisoned_turn = 0

    def next_turn(self, battle):
        if not self.current:
            return ""
        if self.current == "b-poison":
            self.badly_poisoned_turn += 1
        if self.pokemon.ability() == Ability.HYDRATION and battle.weather.get() in ("rain", "h-rain"):
            removed = self.current
            self.reset()
            return f"{self.pokemon.name}'s hydration cured its {removed}!\n"
        if self.pokemon.ability() == Ability.SHED_SKIN and not random.randint(0, 2):
            removed = self.current
            self.reset()
            return f"{self.pokemon.name}'s shed skin cured its {removed}!\n"
        if self.current == "burn":
            damage = max(1, self.pokemon.starting_hp // 16)
            if self.pokemon.ability() == Ability.HEATPROOF:
                damage //= 2
            return self.pokemon.damage(damage, battle, source="its burn")
        if self.current == "b-poison":
            if self.pokemon.ability() == Ability.POISON_HEAL:
                return self.pokemon.heal(self.pokemon.starting_hp // 8, source="its poison heal")
            damage = max(1, (self.pokemon.starting_hp // 16) * min(15, self.badly_poisoned_turn))
            return self.pokemon.damage(damage, battle, source="its bad poison")
        if self.current == "poison":
            if self.pokemon.ability() == Ability.POISON_HEAL:
                return self.pokemon.heal(self.pokemon.starting_hp // 8, source="its poison heal")
            damage = max(1, self.pokemon.starting_hp // 8)
            return self.pokemon.damage(damage, battle, source="its poison")
        if self.current == "sleep" and self.pokemon.nightmare:
            return self.pokemon.damage(self.pokemon.starting_hp // 4, battle, source="its nightmare")
        return ""

    def burn(self):
        return self.current == "burn"

    def sleep(self):
        if self.pokemon.ability() == Ability.COMATOSE:
            return True
        return self.current == "sleep"

    def poison(self):
        return self.current in ("poison", "b-poison")

    def paralysis(self):
        return self.current == "paralysis"

    def freeze(self):
        return self.current == "freeze"

    def apply_status(self, status, battle, *, attacker=None, move=None, turns=None, force=False, source: str = ""):
        msg = ""
        if source:
            source = f" from {source}"
        if self.current and not force:
            return f"{self.pokemon.name} already has a status, it can't get {status} too!\n"
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.COMATOSE:
            return f"{self.pokemon.name} already has a status, it can't get {status} too!\n"
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.PURIFYING_SALT:
            return f"{self.pokemon.name}'s purifying salt protects it from being inflicted with {status}!\n"
        if self.pokemon.ability(attacker=attacker, move=move) == Ability.LEAF_GUARD and battle.weather.get() in ("sun",
                                                                                                                 "h-sun"):
            return f"{self.pokemon.name}'s leaf guard protects it from being inflicted with {status}!\n"
        if self.pokemon.substitute and attacker is not self.pokemon and (
                move is None or move.is_affected_by_substitute()):
            return f"{self.pokemon.name}'s substitute protects it from being inflicted with {status}!\n"
        if self.pokemon.owner.safeguard.active() and attacker is not self.pokemon and (
                attacker is None or attacker.ability() != Ability.INFILTRATOR):
            return f"{self.pokemon.name}'s safeguard protects it from being inflicted with {status}!\n"
        if self.pokemon.grounded(battle, attacker=attacker, move=move) and battle.terrain.item == "misty":
            return f"The misty terrain protects {self.pokemon.name} from being inflicted with {status}!\n"
        if self.pokemon.ability(attacker=attacker,
                                move=move) == Ability.FLOWER_VEIL and ElementType.GRASS in self.pokemon.type_ids:
            return f"{self.pokemon.name}'s flower veil protects it from being inflicted with {status}!\n"
        if self.pokemon._name == "Minior":
            return "Minior's hard shell protects it from status effects!\n"
        if status == "burn":
            if ElementType.FIRE in self.pokemon.type_ids:
                return f"{self.pokemon.name} is a fire type and can't be burned!\n"
            if self.pokemon.ability(attacker=attacker, move=move) in (Ability.WATER_VEIL, Ability.WATER_BUBBLE):
                ability_name = Ability(self.pokemon.ability_id).pretty_name
                return f"{self.pokemon.name}'s {ability_name} prevents it from getting burned!\n"
            self.current = status
            msg += f"{self.pokemon.name} was burned{source}!\n"
        if status == "sleep":
            if self.pokemon.ability(attacker=attacker, move=move) in (Ability.INSOMNIA, Ability.VITAL_SPIRIT,
                                                                      Ability.SWEET_VEIL):
                ability_name = Ability(self.pokemon.ability_id).pretty_name
                return f"{self.pokemon.name}'s {ability_name} keeps it awake!\n"
            if self.pokemon.grounded(battle, attacker=attacker, move=move) and battle.terrain.item == "electric":
                return f"The terrain is too electric for {self.pokemon.name} to fall asleep!\n"
            if battle.trainer1.current_pokemon and battle.trainer1.current_pokemon.uproar.active():
                return f"An uproar keeps {self.pokemon.name} from falling asleep!\n"
            if battle.trainer2.current_pokemon and battle.trainer2.current_pokemon.uproar.active():
                return f"An uproar keeps {self.pokemon.name} from falling asleep!\n"
            if turns is None:
                turns = random.randint(2, 4)
            if self.pokemon.ability(attacker=attacker, move=move) == Ability.EARLY_BIRD:
                turns //= 2
            self.current = status
            self.sleep_timer.set_turns(turns)
            msg += f"{self.pokemon.name} fell asleep{source}!\n"
        if status in ("poison", "b-poison"):
            if attacker is None or attacker.ability() != Ability.CORROSION:
                if ElementType.STEEL in self.pokemon.type_ids:
                    return f"{self.pokemon.name} is a steel type and can't be poisoned!\n"
                if ElementType.POISON in self.pokemon.type_ids:
                    return f"{self.pokemon.name} is a poison type and can't be poisoned!\n"
            if self.pokemon.ability(attacker=attacker, move=move) in (Ability.IMMUNITY, Ability.PASTEL_VEIL):
                ability_name = Ability(self.pokemon.ability_id).pretty_name
                return f"{self.pokemon.name}'s {ability_name} keeps it from being poisoned!\n"
            self.current = status
            bad = " badly" if status == "b-poison" else ""
            msg += f"{self.pokemon.name} was{bad} poisoned{source}!\n"

            if move is not None and attacker is not None and attacker.ability() == Ability.POISON_PUPPETEER:
                msg += self.pokemon.confuse(attacker=attacker, source=f"{attacker.name}'s poison puppeteer")
        if status == "paralysis":
            if ElementType.ELECTRIC in self.pokemon.type_ids:
                return f"{self.pokemon.name} is an electric type and can't be paralyzed!\n"
            if self.pokemon.ability(attacker=attacker, move=move) == Ability.LIMBER:
                return f"{self.pokemon.name}'s limber keeps it from being paralyzed!\n"
            self.current = status
            msg += f"{self.pokemon.name} was paralyzed{source}!\n"
        if status == "freeze":
            if ElementType.ICE in self.pokemon.type_ids:
                return f"{self.pokemon.name} is an ice type and can't be frozen!\n"
            if self.pokemon.ability(attacker=attacker, move=move) == Ability.MAGMA_ARMOR:
                return f"{self.pokemon.name}'s magma armor keeps it from being frozen!\n"
            if battle.weather.get() in ("sun", "h-sun"):
                return f"It's too sunny to freeze {self.pokemon.name}!\n"
            self.current = status
            msg += f"{self.pokemon.name} was frozen solid{source}!\n"

        if self.pokemon.ability(attacker=attacker, move=move) == Ability.SYNCHRONIZE and attacker is not None:
            msg += attacker.nv.apply_status(status, battle, attacker=self.pokemon,
                                            source=f"{self.pokemon.name}'s synchronize")

        if self.pokemon.held_item.should_eat_berry_status(attacker):
            msg += self.pokemon.held_item.eat_berry(attacker=attacker, move=move)

        return msg

    def reset(self):
        self.current = ""
        self.badly_poisoned_turn = 0
        self.sleep_timer.set_turns(0)
        self.pokemon.nightmare = False