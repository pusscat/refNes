class Instruction(object):
    def __init__(self, mnem, function, size, cycles):
        self.mnem = mnem
        self.function = function
        self.cycles = cycles
        self.size = size

    def execute(cpu):
        self.function(cpu)
        cpu.incPC(self.size)
        cpu.incCycles(self.cycles)


def adcImm(cpu):
    pass

def adcZero(cpu):
    pass

def adcZeroX(cpu):
    pass

# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - Appendix A
                # opcode : Instruction(mnem, function, size, cycles), 
instructions = {0x69: Instruction('ADCimm', adcImm, 2, 2),
                0x65: Instruction('ADCzero', adcZero, 2, 3),
                0x75: Instruction('ADCzerox', adcZeroX, 2, 4),
                }
