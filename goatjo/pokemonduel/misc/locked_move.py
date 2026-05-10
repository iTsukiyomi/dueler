from .expiring_effect import ExpiringEffect


class LockedMove(ExpiringEffect):

    def __init__(self, move, turns_to_expire: int):
        super().__init__(turns_to_expire)
        self.move = move
        self.turn = 0

    def next_turn(self):
        expired = super().next_turn()
        self.turn += 1
        return expired

    def is_last_turn(self):
        return self._remaining_turns == 1