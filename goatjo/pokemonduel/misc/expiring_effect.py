import random
from ..enums import Ability, ElementType


class ExpiringEffect():

    def __init__(self, turns_to_expire: int):
        self._remaining_turns = turns_to_expire

    def active(self):
        if self._remaining_turns is None:
            return True
        return bool(self._remaining_turns)

    def next_turn(self):
        if self._remaining_turns is None:
            return False
        if self.active():
            self._remaining_turns -= 1
            return not self.active()
        return False

    def set_turns(self, turns_to_expire):
        self._remaining_turns = turns_to_expire