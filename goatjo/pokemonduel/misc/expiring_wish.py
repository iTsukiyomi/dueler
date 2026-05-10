from .expiring_effect import ExpiringEffect


class ExpiringWish(ExpiringEffect):

    def __init__(self):
        super().__init__(0)
        self.hp = None

    def next_turn(self):
        expired = super().next_turn()
        hp = 0
        if expired:
            hp = self.hp
            self.hp = None
        return hp

    def set(self, hp):
        self.hp = hp
        self._remaining_turns = 2