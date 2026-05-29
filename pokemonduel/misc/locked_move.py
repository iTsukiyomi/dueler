from .expiring_effect import ExpiringEffect


class LockedMove(ExpiringEffect):
    """A multi-turn move that a pokemon is locked into."""

    def __init__(self, move, turns_to_expire: int):
        super().__init__(turns_to_expire)
        self.move = move
        self.turn = 0

    def next_turn(self):
        """Progresses the move a turn."""
        expired = super().next_turn()
        self.turn += 1
        return expired

    def is_last_turn(self):
        """Returns True if this is the last turn this move will be used."""
        return self._remaining_turns == 1
