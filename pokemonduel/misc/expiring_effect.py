import random
from ..enums import Ability, ElementType


class ExpiringEffect():
    """
    Some effect that has a specific amount of time it is active.

    turns_to_expire can be None, in which case this effect never expires.
    """

    def __init__(self, turns_to_expire: int):
        self._remaining_turns = turns_to_expire

    def active(self):
        """Returns True if this effect is still active, False otherwise."""
        if self._remaining_turns is None:
            return True
        return bool(self._remaining_turns)

    def next_turn(self):
        """
        Progresses this effect for a turn.

        Returns True if the effect just ended.
        """
        if self._remaining_turns is None:
            return False
        if self.active():
            self._remaining_turns -= 1
            return not self.active()
        return False

    def set_turns(self, turns_to_expire):
        """Set the amount of turns until this effect expires."""
        self._remaining_turns = turns_to_expire
