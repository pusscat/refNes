class Instruction(object):
    def __init__(self, mnem, function, cycles, size):
        self.mnem = mnem
        self.function = function
        self.cycles = cycles
        self.size = size

    def execute(cpu):
        self.function(cpu)
        cpu.incPC(self.size)
        cpu.incCycles(self.cycles)




                # opcode : Instruction(mnem, function, cycles, size), 
instructions = {}
