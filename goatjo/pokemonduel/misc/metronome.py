class Metronome():
    """Holds recent move status for the held item metronome."""

    def __init__(self):
        self.move = ""
        self.count = 0

    def reset(self):
        """A move failed or a non-move action was done."""
        self.move = ""
        self.count = 0

    def use(self, movename):
        """Updates the metronome based on a used move."""
        if self.move == movename:
            self.count += 1
        else:
            self.move = movename
            self.count = 1

    def get_buff(self, movename):
        """Get the buff multiplier for this metronome."""
        if self.move != movename:
            return 1
        return min(2, 1 + (.2 * self.count))
