class Instruction(object):
    def __init__(self, mnem, function, operType, size, cycles):
        global flags

        self.mnem = mnem
        self.function = function
        self.operType = operType
        self.flags = flags[mnem]
        self.cycles = cycles
        self.extraCycles = 0
        self.size = size

    def execute(cpu):
        # emulate the instruction and add instruction size to PC
        # if the function returns false implying it hasnt changed PC
        if self.function(cpu, instruction) is False:
            cpu.incPC(self.size)
        cpu.incCycles(self.cycles + self.extraCycles)
        self.extraCycles = 0

    def addCycles(cycles):
        self.extraCycles = cycles

# instruction functions return True if they modify PC
# return false otherwise

def GetValue(cpu, instruction, operType):
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
        lowOrder = cpu.ReadRelPC(1) + cpu.GetRegister('X')
        if lowOrder > 0xFF:
            instruction.addCycles(1)
        return cpu.ReadMemory(cpu.ReadRelPC(2) << 8 + lowOrder)
    if operType is 'ABSY':
        lowOrder = cpu.ReadRelPC(1) + cpu.GetRegister('Y')
        if lowOrder > 0xFF:
            instruction.addCycles(1)
        return cpu.ReadMemory(cpu.ReadRelPC(2) << 8 + lowOrder)
    if operType is 'INDX':
        addrPtr = ((cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF)
        return cpu.ReadMemory(cpu.ReadMemory(addrPtr+1) << 8 + cpu.ReadMemory(addrPtr))
    if operType is 'INDY':
        highOrder = cpu.ReadMemory(cpu.ReadRelPC(1)+1) << 8
        lowOrder = cpu.ReadMemory(cpu.ReadRelPC(1)) + cpu.GetRegister('Y')
        if lowOrder > 0xFF:
           instruction.addCycles(1)
        return cpu.ReadMemory(highOrder + lowOrder)
    if operType is 'PCREL':
        return cpu.ReadRelPC(1) + cpu.GetRegister('PC')
    return value

def GetAddress(cpu, instruction, operType):
    if operType is 'ZERO':
        return cpu.ReadRelPC(1)
    if operType is 'ZEROX':
        return (cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF
    if operType is 'ABS':
        return cpu.ReadRelPC(2) << 8 + cpu.ReadRelPC(1)
    if operType is 'ABSX':
        if 
        return cpu.ReadRelPC(2) << 8 + cpu.ReadRelPC(1) + cpu.GetRegister('X')
    return address


def doAdc(cpu, instruction):
    value = GetValue(cpu, self.operType)
    accuVal = cpu.GetRegister('A')
    carryVal = 1 if cpu.GetFlag('C') else 0

    newVal = accuVal + value + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, immVal, newVal, False, False)
    return False

def doAnd(cpu, instruction):
    value = GetValue(cpu, self.operType)
    accuVal = cpu.GetRegister('A')

    newVal = accuVal & immVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, immVal, newVal, False, False)
    return False

def doAsl(cpu, instruction):
    addrVal = GetAddress(cpu, self.operType)
    memVal = cpu.ReadMemory(address)

    newVal = memVal << 1

    if newVal > 0xFF:
        cpu.SetFlag('C')
    cpu.SetMemory(address, newVal)
    cpu.UpdateFlags(intruction.flags, memVal, memVal, newVal, False, False)
    return False

def doAslAccu(cpu, instruction):
    accuVal = cpu.GetRegister('A')

    newVal = accuVal << 1

    if newVal > 0xFF:
       cpu.SetFlag('C')

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(intruction.flags, accuVal, accuVal, newVal, False, False)
    return False


def doBranch(cpu, instruction, flag, value):
    flagVal = cpu.GetFlag(flag)
    if flagVal is not value:
        return False

    target = cpu.GetValue(cpu, 'PCREL')
    currPC = cpu.GetRegister('PC')
    cpu.SetPC(target)
   
    # Add 1 cycle because we branched - add an extra if we jumped a page boundary
    if target & 0xFF00 != currPC & 0xFF00:
        instruction.addCycles(2)
    else:
        instruction.addCycles(1)

    return True         # true because we change PC in this case

def doBcc(cpu, instruction):
    return doBranch(cpu, instruction, 'C', False)

def doBcs(cpu, instruction):
    return doBranch(cpu, instruction, 'C', True)

def doBeq(cpu, instruction):
    return doBranch(cpu, instruction, 'Z', True)

def doBit(cpu, instruction):
    value = cpu.GetValue(instruction.operType)
    accuVal = cpu.GetRegister('A')

    cpu.SetFlag('N', (value & (1 << 7)) >> 7)
    cpu.SetFlag('V', (value & (1 << 6)) >> 6)
    cpu.SetFlag('Z', 1 if value & accuVal != 0 else 0)
    return False

def doBmi(cpu, instruction):
    return doBranch(cpu, instruction, 'N', True)

def doBne(cpu, instruction):
    return doBranch(cpu, instruction, 'Z', False)

def doBpl(cpu, instruction):
    return doBranch(cpu, instruction, 'N', False)

def doBrk(cpu, instruction):
    cpu.SetFlag('B', 1)
    cpu.PushWord(cpu.GetRegister('PC')+2)
    cpu.PushByte(cpu.GetRegister('S'))
    return False

def doBvc(cpu, instruction):
    return doBranch(cpu, instruction, 'V', False)

def doBvs(cpu, instruction):
    return doBranch(cpu, instruction, 'V', True)

def doClc(cpu, instruction):
    cpu.SetFlag('C', 0)
    return False

def doCld(cpu, instruction):
    cpu.SetFlag('D', 0)
    return False

def doCli(cpu, instruction):
    cpu.SetFlag('I', 0)
    return False

def doClv(cpu, instruction):
    cpu.SetFlag('V', 0)
    return False

# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - Appendix A
flags = {   'ADC': ['N', 'Z', 'C', 'V'],
            'AND': ['N', 'Z'],
            'ASL': ['N', 'Z'], #set C manually
            'BCC': [],
            'BCS': [],
            'BEQ': [],
            'BIT': [],
            'BMI': [],
            'BNE': [],
            'BPL': [],
            'BRK': [],
            'BVC': [],
            'BVS': [],
            'CLC': [],
            'CLD': [],
            'CLI': [],
            'CLV': [],
        }

           # opcode : Instruction(mnem, function, size, cycles), 
instructions = {0x69: Instruction('ADC', doAdc, 'IMM', 2, 2),
                0x65: Instruction('ADC', doAdc, 'ZERO',  2, 3),
                0x75: Instruction('ADC', doAdc, 'ZEROX', 2, 4),
                0x6D: Instruction('ADC', doAdc, 'ABS', 3, 4),
                0x7D: Instruction('ADC', doAdc, 'ABSX', 3, 4),
                0x79: Instruction('ADC', doAdc, 'ABSY', 3, 4),
                0x61: Instruction('ADC', doAdc, 'INDX', 2, 6),
                0x71: Instruction('ADC', doAdc, 'INDY', 2, 5),
                0x29: Instruction('AND', doAnd, 'IMM', 2, 2),
                0x25: Instruction('AND', doAnd, 'ZERO', 2, 3),
                0x35: Instruction('AND', doAnd, 'ZEROX', 2, 4),
                0x2d: Instruction('AND', doAnd, 'ABS', 3, 4),
                0x3d: Instruction('AND', doAnd, 'ABSX', 3, 4),
                0x39: Instruction('AND', doAnd, 'ABSY', 3, 4),
                0x21: Instruction('AND', doAnd, 'INDX', 2, 6),
                0x31: Instruction('AND', doAnd, 'INDY', 2, 5),
                0x0A: Instruction('ASL', doAslAccu, '', 1, 2),
                0x06: Instruction('ASL', doAsl, 'ZERO', 2, 5),
                0x16: Instruction('ASL', doAsl, 'ZEROX', 2, 6),
                0x0E: Instruction('ASL', doAsl, 'ABS', 3, 6),
                0x1E: Instruction('ASL', doAsl, 'ABSX', 3, 7),
                0x90: Instruction('BCC', doBcc, 'PCREL', 2, 2),
                0xB0: Instruction('BCS', doBcs, 'PCREL', 2, 2),
                0xF0: Instruction('BEQ', doBeq, 'PCREL', 2, 2),
                0x24: Instruction('BIT', doBeq, 'ZERO', 2, 3),
                0x2C: Instruction('BIT', doBeq, 'ABS', 3, 4),
                0x30: Instruction('BMI', doBmi, 'PCREL', 2, 2),
                0xD0: Instruction('BNE', doBne, 'PCREL', 2, 2),
                0x10: Instruction('BPL', doBpl, 'PCREL', 2, 2),
                0x00: Instruction('BRK', doBrk, '', 1, 7),
                0x50: Instruction('BVC', doBvc, 'PCREL', 2, 2),
                0x70: Instruction('BVS', doBvs, 'PCREL', 2, 2),
                0x18: Instruction('CLC', doClc, '', 1, 2),
                0xD8: Instruction('CLD', doCld, '', 1, 2),
                0x58: Instruction('CLI', doCli, '', 1, 2),
                0xB8: Instruction('CLV', doClv, '', 1, 2),
                }
