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

def GetValue(cpu, operType):
    if operType is 'IMM':
        return cpu.ReadRelPC(1)
    if operType is 'ZERO':
        return cpu.ReadMemory(cpu.ReadRelPC(1))
    if operType is 'ZEROX' or operType is 'INDX':
        return cpu.ReadMemory((cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF)
    if operType is 'ZEROY'
        return cpu.ReadMemory((cpu.ReadRelPC(1) + cpu.GetRegister('Y')) & 0xFF)
    if operType is 'ABS':
        return cpu.ReadMemory(cpu.ReadRelPC(2) << 8 + cpu.ReadRelPC(1))
    if operType is 'ABSX':
        return cpu.ReadMemory(cpu.ReadRelPC(2) << 8 + cpu.ReadRelPC(1) + cpu.GetRegister('X'))
    if operType is 'ABSY':
        return cpu.ReadMemory(cpu.ReadRelPC(2) << 8 + cpu.ReadRelPC(1) + cpu.GetRegister('Y'))
    if operType is 'INDX':
        addrPtr = ((cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF)
        return cpu.ReadMemory(cpu.ReadMemory(addrPtr+1) << 8 + cpu.ReadMemory(addrPtr))
    if operType is 'INDY':
        addrPtr = ((cpu.ReadRelPC(1) + cpu.GetRegister('Y')) & 0xFF)
        return cpu.ReadMemory(cpu.ReadMemory(addrPtr+1) << 8 + cpu.ReadMemory(addrPtr))
    return value

def GetAddress(cpu, operType):
    return address


def adcImm(cpu, instruction):
    immVal = GetValue(cpu, 'IMM')
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + immVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, immVal, newVal, False, False)
    return False

def adcZero(cpu, instruction):
    zeroOffset = GetValue(cpu, 'ZERO')
    memVal = cpu.ReadMemory(zeroOffset)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcZeroX(cpu, instruction):
    memVal = GetValue(cpu, 'ZEROX')

    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcAbs(cpu, instruction):
    memVal = GetValue(cpu, 'ABS')
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcAbsX(cpu, instruction):
    memVal = GetValue(cpu, 'ABSX')
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcAbsY(cpu, instruction):
    memVal = GetValue(cpu, 'ABSY')
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False


def adcIndX(cpu, instruction):
    memVal = GetValue(cpu, 'INDX')
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + memVal + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, memVal, newVal, False, False)
    return False

def adcIndY(cpu, instruction):
    memVal = GetValue(cpu, 'INDY')
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
                0x61: Instruction('ADCindX', adcIndX, flags['ADC'], 2, 6),
                0x71: Instruction('ADCindY', adcIndY, flags['ADC'], 2, 5),
                }
