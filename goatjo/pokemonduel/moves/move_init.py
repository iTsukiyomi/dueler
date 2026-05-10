from ..enums import Ability, DamageClass, ElementType, MoveTarget


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
        """Sets up anything this move needs to do prior to normal move execution."""
        msg = ""
        if self.effect == 129 and (isinstance(defender.owner.selected_action, int) or defender.owner.selected_action.effect in (128, 154, 229, 347, 493)):
            msg += self.use(attacker, defender, battle)
        if self.effect == 171:
            msg += f"{attacker.name} is focusing on its attack!\n"
        if self.effect == 404:
            attacker.beak_blast = True
        return msg

    def get_priority(self, attacker, defender, battle):
        """Get the priority of this move."""
        return self.priority

    def get_effect_chance(self, attacker, defender, battle):
        """Get the effect chance of this move."""
        return self.effect_chance