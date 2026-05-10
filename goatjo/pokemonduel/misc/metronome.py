class Metronome():

    def __init__(self):
        self.move = ""
        self.count = 0

    def reset(self):
        self.move = ""
        self.count = 0

    def use(self, movename):
        if self.move == movename:
            self.count += 1
        else:
            self.move = movename
            self.count = 1

    def get_buff(self, movename):
        if self.move != movename:
            return 1
        return min(2, 1 + (.2 * self.count))