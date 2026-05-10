from .expiring_effect import ExpiringEffect


class ExpiringItem(ExpiringEffect):

    def __init__(self):
        super().__init__(0)
        self.item = None

    def next_turn(self):
        expired = super().next_turn()
        if expired:
            self.item = None
        return expired

    def set(self, item, turns: int):
        self.item = item
        self._remaining_turns = turns

    def end(self):
        self.item = None
        super().end()

    def active(self):
        return self.item is not None and super().active()