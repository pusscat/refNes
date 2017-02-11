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
    if operType is 'ZERO':
        return cpu.ReadRelPC(1)
    if operType is 'ZEROX':
        return (cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF
    if operType is 'ABS':
        return cpu.ReadRelPC(2) << 8 + cpu.ReadRelPC(1)
    if operType is 'ABSX':
        return cpu.ReadRelPC(2) << 8 + cpu.ReadRelPC(1) + cpu.GetRegister('X')
    return address


def doAdc(cpu, instruction, value):
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + value + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, immVal, newVal, False, False)
    return False


def adcImm(cpu, instruction):
    immVal = GetValue(cpu, 'IMM')
    return doAdc(cpu, instruction, immVal)

def adcZero(cpu, instruction):
    memVal= GetValue(cpu, 'ZERO')
    return doAdc(cpu, instruction, memVal)

def adcZeroX(cpu, instruction):
    memVal = GetValue(cpu, 'ZEROX')
    return doAdc(cpu, instruction, memVal)

def adcAbs(cpu, instruction):
    memVal = GetValue(cpu, 'ABS')
    return doAdc(cpu, instruction, memVal)

def adcAbsX(cpu, instruction):
    memVal = GetValue(cpu, 'ABSX')
    return doAdc(cpu, instruction, memVal)

def adcAbsY(cpu, instruction):
    memVal = GetValue(cpu, 'ABSY')
    return doAdc(cpu, instruction, memVal)

def adcIndX(cpu, instruction):
    memVal = GetValue(cpu, 'INDX')
    return doAdc(cpu, instruction, memVal)

def adcIndY(cpu, instruction):
    memVal = GetValue(cpu, 'INDY')
    return doAdc(cpu, instruction, memVal)

def doAnd(cpu, instruction, value):
    accuVal = cpu.GetRegister('A')

    newVal = accuVal & immVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, immVal, newVal, False, False)
    return False

def andImm(cpu, instruction):
    immVal = GetValue(cpu, 'IMM')
    return doAnd(cpu, instruction, immVal)

def andZero(cpu, instruction):
    memVal = GetValue(cpu, 'ZERO')
    return doAnd(cpu, instruction, memVal)

def andZeroX(cpu, instruction):
    memVal = GetValue(cpu, 'ZEROX')
    return doAnd(cpu, instruction, memVal)

def andAbs(cpu, instruction):
    memVal = GetValue(cpu, 'ABS')
    return doAnd(cpu, instruction, memVal)

def andAbsX(cpu, instruction):
    memVal = GetValue(cpu, 'ABSX')
    return doAnd(cpu, instruction, memVal)

def andAbsY(cpu, instruction):
    memVal = GetValue(cpu, 'ABSY')
    return doAnd(cpu, instruction, memVal)

def andIndX(cpu, instruction):
    memVal = GetValue(cpu, 'INDX')
    return doAnd(cpu, instruction, memVal)

def andIndY(cpu, instruction):
    memVal = GetValue(cpu, 'INDY')
    return doAnd(cpu, instruction, memVal)

def doAsl(cpu, instruction, address):
    memVal = cpu.ReadMemory(address)

    newVal = memVal << 1

    if newVal > 0xFF:
        cpu.SetFlag('C')
    cpu.SetMemory(address, newVal)
    cpu.UpdateFlags(intruction.flags, memVal, memVal, newVal, False, False)
    return False

def aslAccu(cpu, instruction):
    accuVal = cpu.GetRegister('A')

    newVal = accuVal << 1

    if newVal > 0xFF:
       cpu.SetFlag('C')

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(intruction.flags, accuVal, accuVal, newVal, False, False)
    return False

def aslZero(cpu, instruction):
    addrVal = GetAddress(cpu, 'ZERO')
    return doAsl(cpu, instruction, addrVal)

def aslZeroX(cpu, instruction):
    addrVal = GetAddress(cpu, 'ZEROX')
    return doAsl(cpu, instruction, addrVal)

def aslAbs(cpu, instruction):
    addrVal = GetAddress(cpu, 'ABS')
    return doAsl(cpu, instruction, addrVal)

def aslAbsX(cpu, instruction):
    addrVal = GetAddress(cpu, 'ABSX')
    return doAsl(cpu, instruction, addrVal)




# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - Appendix A
flags = {   'ADC', ['N', 'Z', 'C', 'V'],
            'AND', ['N', 'Z'],
            'ASL', ['N', 'Z'], #set C manually
        }

           # opcode : Instruction(mnem, function, size, cycles), 
instructions = {0x69: Instruction('ADCimm', adcImm, flags['ADC'], 2, 2),
                0x65: Instruction('ADCzero', adcZero, flags['ADC'], 2, 3),
                0x75: Instruction('ADCzeroX', adcZeroX, flags['ADC'], 2, 4),
                0x6D: Instruction('ADCabs', adcAbs, flags['ADC'], 3, 4),
                0x7D: Instruction('ADCabsX', adcAbsX, flags['ADC'], 3, 4),
                0x79: Instruction('ADCabsY', adcAbsY, flags['ADC'], 3, 4),
                0x61: Instruction('ADCindX', adcIndX, flags['ADC'], 2, 6),
                0x71: Instruction('ADCindY', adcIndY, flags['ADC'], 2, 5),
                0x29: Instruction('ANDimm', andImm, flags['AND'], 2, 2),
                0x25: Instruction('ANDzero', andImm, flags['AND'], 2, 3),
                0x35: Instruction('ANDzeroX', andImm, flags['AND'], 2, 4),
                0x2d: Instruction('ANDabs', andImm, flags['AND'], 3, 4),
                0x3d: Instruction('ANDabsX', andImm, flags['AND'], 3, 4),
                0x39: Instruction('ANDabsY', andImm, flags['AND'], 3, 4),
                0x21: Instruction('ANDindX', andImm, flags['AND'], 2, 6),
                0x31: Instruction('ANDindY', andImm, flags['AND'], 2, 5),
                0x0A: Instruction('ASLaccu', aslAccu, flags['ASL'], 1, 2),
                0x06: Instruction('ASLzero', aslZero, flags['ASL'], 2, 5),
                0x16: Instruction('ASLzeroX', aslZeroX, flags['ASL'], 2, 6),
                0x0E: Instruction('ASLabs', aslAbs, flags['ASL'], 3, 6),
                0x1E: Instruction('ASLabsX', aslAbsX, flags['ASL'], 3, 7),
                }
