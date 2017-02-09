class Instruction(object):
    def __init__(self, mnem, function, size, cycles):
        self.mnem = mnem
        self.function = function
        self.cycles = cycles
        self.size = size

    def execute(cpu):
        # emulate the instruction and add instruction size to PC
        # if the function returns false implying it hasnt changed PC
        if self.function(cpu) is False:
            cpu.incPC(self.size)
        cpu.incCycles(self.cycles)

# instruction functions return True if they modify PC
# return false otherwise

def adcImm(cpu):
    immVal = cpu.ReadRelPC(1)
    accuVal = cpu.GetRegister('A')

    cpu.SetRegister('A', accuVal + immVal)
    return False

def adcZero(cpu):
    zeroOffset = cpu.ReadRelPC(1)
    memVal = cpu.ReadMemory(zeroOffset)
    accuVal = cpu.GetRegister('A')

    cpu.SetRegister('A', accuVal + memVal)
    return False

def adcZeroX(cpu):
    zeroOffset = cpu.ReadRelPC(1)
    xVal = cpu.GetRegister('X')

    memVal = cpu.ReadMemory(zeroOffset + xVal)
    accuVal = cpu.GetRegister('A')

    cpu.SetRegister('A', accuVal + memVal)
    return False


# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - Appendix A
                # opcode : Instruction(mnem, function, size, cycles), 
instructions = {0x69: Instruction('ADCimm', adcImm, 2, 2),
                0x65: Instruction('ADCzero', adcZero, 2, 3),
                0x75: Instruction('ADCzerox', adcZeroX, 2, 4),
                }
