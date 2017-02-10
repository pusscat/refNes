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
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + immVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, immVal, newVal, False, False)
    return False

def adcZero(cpu, instruction):
    zeroOffset = cpu.ReadRelPC(1)
    memVal = cpu.ReadMemory(zeroOffset)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcZeroX(cpu, instruction):
    zeroOffset = cpu.ReadRelPC(1)
    xVal = cpu.GetRegister('X')

    # because its Zero page relative, this address wraps if it goes past $00FF
    memVal = cpu.ReadMemory((zeroOffset + xVal) & 0xFF)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcAbs(cpu, instruction):
    # 6502 is little endian, so next byte is least sig, one after is most sig
    absOffset = cpu.ReadRelPc(2) << 8 + cpu.ReadRelPc(1)
    memVal = cpu.ReadMemory(absOffset)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcAbsX(cpu, instruction):
    # 6502 is little endian, so next byte is least sig, one after is most sig
    absOffset = cpu.ReadRelPc(2) << 8 + cpu.ReadRelPc(1)
    xVal = cpu.GetRegister('X')
    memVal = cpu.ReadMemory(absOffset + xVal)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcAbsY(cpu, instruction):
    # 6502 is little endian, so next byte is least sig, one after is most sig
    absOffset = cpu.ReadRelPc(2) << 8 + cpu.ReadRelPc(1)
    yVal = cpu.GetRegister('Y')
    memVal = cpu.ReadMemory(absOffset + yVal)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False


def adcIndY(cpu, instruction):
    zeroOffset = cpu.ReadRelPC(1)
    yVal = cpu.GetRegister('Y')

    # ASSUMING THE FOLLOWING:
    # because its Zero page relative, this address wraps if it goes past $00FF
    memVal = cpu.ReadMemory((zeroOffset + yVal) & 0xFF)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - Appendix A
                # opcode : Instruction(mnem, function, size, cycles), 
flags = {   'ADC', ['N', 'Z', 'C', 'V'] }

instructions = {0x69: Instruction('ADCimm', adcImm, flags['ADC'], 2, 2),
                0x65: Instruction('ADCzero', adcZero, flags['ADC'], 2, 3),
                0x75: Instruction('ADCzeroX', adcZeroX, flags['ADC'], 2, 4),
                0x6D: Instruction('ADCabs', adcAbs, flags['ADC'], 3, 4),
                0x7D: Instruction('ADCabsX', adcAbsX, flags['ADC'], 3, 4),
                0x79: Instruction('ADCabsY', adcAbsY, flags['ADC'], 3, 4),
                0x61: Instruction('ADCindX', adcZeroX, flags['ADC'], 2, 6),
                0x71: Instruction('ADCindY', adcIndY, flags['ADC'], 2, 5),
                }
