class Instruction(object):
    def __init__(self, mnem, function, flags, size, cycles):
        self.mnem = mnem
        self.function = function
        self.flags = flags
        self.cycles = cycles
        self.size = size

    def execute(cpu):
        # emulate the instruction and add instruction size to PC
        # if the function returns false implying it hasnt changed PC
        if self.function(cpu, instruction) is False:
            cpu.incPC(self.size)
        cpu.incCycles(self.cycles)

# instruction functions return True if they modify PC
# return false otherwise

def adcImm(cpu, instruction):
    immVal = cpu.ReadRelPC(1)
    accuVal = cpu.GetRegister('A')
    if cpu.GetFlag('C') carryVal = 1 else carryVal = 0

    newVal = accuVal + immVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, immVal, newVal, False, False)
    return False

def adcZero(cpu, instruction):
    zeroOffset = cpu.ReadRelPC(1)
    memVal = cpu.ReadMemory(zeroOffset)
    accuVal = cpu.GetRegister('A')
    if cpu.GetFlag('C') carryVal = 1 else carryVal = 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcZeroX(cpu, instruction):
    zeroOffset = cpu.ReadRelPC(1)
    xVal = cpu.GetRegister('X')

    memVal = cpu.ReadMemory(zeroOffset + xVal)
    accuVal = cpu.GetRegister('A')
    if cpu.GetFlag('C') carryVal = 1 else carryVal = 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False


# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - Appendix A
                # opcode : Instruction(mnem, function, size, cycles), 
flags = {   'ADC', ['N', 'Z', 'C', 'V'] }

instructions = {0x69: Instruction('ADCimm', adcImm, flags['ADC'], 2, 2),
                0x65: Instruction('ADCzero', adcZero, flags['ADC'], 2, 3),
                0x75: Instruction('ADCzerox', adcZeroX, flags['ADC'], 2, 4),
                }
