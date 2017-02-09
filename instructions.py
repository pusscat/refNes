class instruction(object):
    def __init__(self, mnem, function, cycles, size):
        self.mnem = mnem
        self.execute = function
        self.cycles = cycles
        self.size = size


