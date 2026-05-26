from .expiring_effect import ExpiringEffect


class ExpiringWish(ExpiringEffect):
    """Stores the HP and when to heal for the move Wish."""

    def __init__(self):
        super().__init__(0)
        self.hp = None

    # pyrefly: ignore [bad-override]
    def next_turn(self):
        """Progresses the effect a turn."""
        expired = super().next_turn()
        hp = 0
        if expired:
            hp = self.hp
            self.hp = None
        return hp

    def set(self, hp):
        """Set the move and turns until expiration."""
        self.hp = hp
        self._remaining_turns = 2
