from .expiring_effect import ExpiringEffect


class ExpiringItem(ExpiringEffect):
    """An expiration timer with some data."""

    def __init__(self):
        super().__init__(0)
        self.item = None

    def next_turn(self):
        """Progresses the effect a turn."""
        expired = super().next_turn()
        if expired:
            self.item = None
        return expired

    def set(self, item, turns: int):
        """Set the item and turns until expiration."""
        self.item = item
        self._remaining_turns = turns

    def end(self):
        """Ends this expiring item."""
        self.item = None
        self._remaining_turns = 0