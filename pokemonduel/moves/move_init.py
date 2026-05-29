from ..enums import Ability, DamageClass, ElementType

class MoveInit:
    """Move initialization and basic properties."""

    def __init__(self, **kwargs):
        """Accepts a dict from the mongo moves table."""
        self.id = kwargs["id"]
        self.name = kwargs["identifier"]
        self.pretty_name = self.name.capitalize().replace("-", " ")
        self.power = kwargs["power"]
        self.pp = kwargs["pp"]
        self.starting_pp = self.pp
        self.accuracy = kwargs["accuracy"]
        self.priority = kwargs["priority"]
        self.type = kwargs["type_id"]
        self.damage_class = kwargs["damage_class_id"]
        self.effect = kwargs["effect_id"]
        self.effect_chance = kwargs["effect_chance"]
        self.target = kwargs["target_id"]
        self.crit_rate = kwargs["crit_rate"]
        self.min_hits = kwargs["min_hits"]
        self.max_hits = kwargs["max_hits"]
        self.used = False

    def setup(self, attacker, defender, battle):
        """
        Sets up anything this move needs to do prior to normal move execution.

        Returns a formatted message.
        """
        msg = ""
        if self.effect == 129 and (isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.effect in (128, 154, 229, 347, 493)):
            # pyrefly: ignore [missing-attribute]
            msg += self.use(attacker, defender, battle)
        if self.effect == 171:
            msg += f"{attacker.name} is focusing on its attack!\n"
        if self.effect == 404:
            attacker.beak_blast = True
        return msg

    def get_priority(self, attacker, defender, battle):
        """
        Calculates the priority value for this move.

        Returns an int priority from -7 to 5.
        """
        priority = self.priority
        # pyrefly: ignore [missing-attribute]
        current_type = self.get_type(attacker, defender, battle)
        if self.effect == 437 and attacker.grounded(battle) and battle.terrain.item == "grassy":
            priority += 1
        if attacker.ability() == Ability.GALE_WINGS and current_type == ElementType.FLYING and attacker.hp == attacker.starting_hp:
            priority += 1
        if attacker.ability() == Ability.PRANKSTER and self.damage_class == DamageClass.STATUS:
            priority += 1
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.TRIAGE and self.is_affected_by_heal_block():
            priority += 3
        return priority

    def get_effect_chance(self, attacker, defender, battle):
        """
        Gets the chance for secondary effects to occur.

        Returns an int from 0-100.
        """
        if self.effect_chance is None:
            return 100
        if defender.ability(attacker=attacker, move=self) == Ability.SHIELD_DUST:
            return 0
        if defender.held_item == "covert-cloak":
            return 0
        if attacker.ability() == Ability.SHEER_FORCE:
            return 0
        if attacker.ability() == Ability.SERENE_GRACE:
            return min(100, self.effect_chance * 2)
        return self.effect_chance
