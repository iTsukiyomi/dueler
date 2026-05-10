class Item:
    """Base class for items."""
    def __init__(self, name):
        self.name = name
        self.battle = None

    def activate_on_switch_in(self, battle):
        return ""

    def activate_end_of_turn(self, battle):
        return ""

    def can_remove(self):
        return True

    def has_item(self):
        return self.name != "none" and self.name != ""

    def use(self):
        pass

    def get_stat_multiplier(self, stat):
        return 1

    def get_speed_multiplier(self):
        return 1

    def should_eat_berry_status(self, attacker):
        return False

    def eat_berry(self, attacker=None, move=None):
        return ""

    def transfer(self, other):
        pass

    def recover(self, other):
        pass

    @property
    def last_used(self):
        return None

    @last_used.setter
    def last_used(self, value):
        pass