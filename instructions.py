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

    def execute(self, cpu):
        # emulate the instruction and add instruction size to PC
        # if the function returns false implying it hasnt changed PC
        if self.function(cpu, self) is False:
            cpu.incPC(self.size)
        cpu.incCycles(self.cycles + self.extraCycles)
        self.extraCycles = 0

    def addCycles(self, cycles):
        self.extraCycles = cycles

# instruction functions return True if they modify PC
# return false otherwise

def GetValue(cpu, instruction):
    operType = instruction.operType
    if operType is 'IMM':
        return cpu.ReadRelPC(1)
    if operType is 'ZERO':
        return cpu.ReadMemory(cpu.ReadRelPC(1))
    if operType is 'ZEROX' or operType is 'INDX': 
        # CANNOT CROSS PAGE BOUNDARY SO MASK READ ADDRESS
        return cpu.ReadMemory(((cpu.ReadRelPC(1) + cpu.GetRegister('X') & 0xFF)) & 0xFF)
    if operType is 'ZEROY':
        return cpu.ReadMemory((cpu.ReadRelPC(1) + cpu.GetRegister('Y')) & 0xFF)
    if operType is 'ABS':
        return cpu.ReadMemory((cpu.ReadRelPC(2) << 8) + cpu.ReadRelPC(1))
    if operType is 'ABSX': # THIS CAN CROSS PAGE BOUNDARY
        lowOrder = cpu.ReadRelPC(1) + cpu.GetRegister('X')
        hiOrder = cpu.ReadRelPC(2)
        if lowOrder > 0xFF:
            instruction.addCycles(1)
        return cpu.ReadMemory((hiOrder << 8) + lowOrder)
    if operType is 'ABSY':
        lowOrder = cpu.ReadRelPC(1) + cpu.GetRegister('Y')
        if lowOrder > 0xFF:
            instruction.addCycles(1)
        return cpu.ReadMemory((cpu.ReadRelPC(2) << 8) + lowOrder)
    if operType is 'INDX':
        addrPtr = ((cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF)
        return cpu.ReadMemory((cpu.ReadMemory(addrPtr+1) << 8) + cpu.ReadMemory(addrPtr))
    if operType is 'INDY':
        highOrder = cpu.ReadMemory(cpu.ReadRelPC(1)+1) << 8
        lowOrder = cpu.ReadMemory(cpu.ReadRelPC(1)) + cpu.GetRegister('Y')
        if lowOrder > 0xFF:
            instruction.addCycles(1)
            # we should NOT add 1 to high order in this case.
        return cpu.ReadMemory(highOrder + lowOrder)
    if operType is 'PCREL':
        pcReg = cpu.GetRegister('PC') + instruction.size
        return ((cpu.ReadRelPC(1) + pcReg) & 0xFF) + (pcReg & 0xFF00)
    return value

def GetAddress(cpu, instruction):
    operType = instruction.operType
    if operType is 'ZERO':
        return cpu.ReadRelPC(1)
    if operType is 'ZEROX':
        return (cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF
    if operType is 'ABS':
        return (cpu.ReadRelPC(2) << 8) + cpu.ReadRelPC(1)
    if operType is 'ABSX':
        return (cpu.ReadRelPC(2) << 8) + cpu.ReadRelPC(1) + cpu.GetRegister('X')
    if operType is 'ABSY':
        return (cpu.ReadRelPC(2) << 8) + cpu.ReadRelPC(1) + cpu.GetRegister('Y')
    if operType is 'IND':
        addr = (cpu.ReadRelPC(2) << 8) + cpu.ReadRelPC(1)
        lowOrder = cpu.ReadMemory(addr)
        if (addr & 0xFF) == 0xFF:
            addr = addr & 0xFF00 # DO NOT WALK PAGE BOUNDARIES
        highOrder = cpu.ReadMemory(addr+1) << 8
        return  cpu.ReadMemory(highOrder + lowOrder)
    if operType is 'INDX':
        addrPtr = ((cpu.ReadRelPC(1) + cpu.GetRegister('X')) & 0xFF)
        return ((cpu.ReadMemory(addrPtr+1) << 8) + cpu.ReadMemory(addrPtr))
    if operType is 'INDY':
        highOrder = cpu.ReadMemory(cpu.ReadRelPC(1)+1) << 8
        lowOrder = cpu.ReadMemory(cpu.ReadRelPC(1)) + cpu.GetRegister('Y')
        if lowOrder > 0xFF:
            instruction.addCycles(1)
            # we should NOT add 1 to high order in this case.
        return (highOrder + lowOrder)

    return None


def doAdc(cpu, instruction):
    value = GetValue(cpu, instruction)
    accuVal = cpu.GetRegister('A')
    carryVal = cpu.GetFlag('C')

    newVal = accuVal + value + carryVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, value, newVal, False)
    return False

def doAnd(cpu, instruction):
    value = GetValue(cpu, instruction)
    accuVal = cpu.GetRegister('A')

    newVal = accuVal & value

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, value, newVal, False)
    return False

def doAsl(cpu, instruction):
    addrVal = GetAddress(cpu, instruction)
    memVal = cpu.ReadMemory(address)

    newVal = memVal << 1

    if newVal > 0xFF:
        cpu.SetFlag('C')
    cpu.SetMemory(address, newVal)
    cpu.UpdateFlags(instruction.flags, memVal, memVal, newVal, False)
    return False

def doAslAccu(cpu, instruction):
    accuVal = cpu.GetRegister('A')

    newVal = accuVal << 1

    if newVal > 0xFF:
       cpu.SetFlag('C')

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, accuVal, accuVal, newVal, False)
    return False


def doBranch(cpu, instruction, flag, value):
    if cpu.GetFlag(flag) is not value:
        return False

    target = GetValue(cpu, instruction)
    currPC = cpu.GetRegister('PC')
    cpu.SetPC(target)
   
    # Add 1 cycle because we branched - add an extra if we jumped a page boundary
    if target & 0xFF00 != currPC & 0xFF00:
        instruction.addCycles(2)
    else:
        instruction.addCycles(1)

    return True         # true because we change PC in this case

def doBcc(cpu, instruction):
    return doBranch(cpu, instruction, 'C', 0)

def doBcs(cpu, instruction):
    return doBranch(cpu, instruction, 'C', 1)

def doBeq(cpu, instruction):
    return doBranch(cpu, instruction, 'Z', 1)

def doBit(cpu, instruction):
    value = GetValue(cpu, instruction)
    accuVal = cpu.GetRegister('A')

    cpu.SetFlag('N', (value & (1 << 7)) >> 7)
    cpu.SetFlag('V', (value & (1 << 6)) >> 6)
    cpu.SetFlag('Z', 1 if value & accuVal != 0 else 0)
    return False

def doBmi(cpu, instruction):
    return doBranch(cpu, instruction, 'N', 1)

def doBne(cpu, instruction):
    return doBranch(cpu, instruction, 'Z', 0)

def doBpl(cpu, instruction):
    return doBranch(cpu, instruction, 'N', 0)

def doBrk(cpu, instruction):
    cpu.PushWord(cpu.GetRegister('PC')+2)
    cpu.PushByte(cpu.GetRegister('S'))
    cpu.SetFlag('I', 1)
    cpu.SetFlag('B', 1)
    
    # jmp to irqBrk vector
    target = cpu.ReadMemWord(cpu.irqBrk)
    cpu.SetPC(target)
    return True

def doBvc(cpu, instruction):
    return doBranch(cpu, instruction, 'V', 0)

def doBvs(cpu, instruction):
    return doBranch(cpu, instruction, 'V', 1)

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

def doCmp(cpu, instruction):
    value = GetValue(cpu, instruction)
    accuVal = cpu.GetRegister('A')
    
    newVal = accuVal - value
    # Dont set a register in compare 
    cpu.UpdateFlags(instruction.flags, accuVal, value, newVal, True)
    return False

def doCpx(cpu, instruction):
    value = GetValue(cpu, instruction)
    xVal = cpu.GetRegister('X')

    newVal = xVal - value
    # Dont set a register in compare 
    cpu.UpdateFlags(instruction.flags, xVal, value, newVal, True)
    return False

def doCpy(cpu, instruction):
    value = GetValue(cpu, instruction)
    yVal = cpu.GetRegister('Y')

    newVal = yVal - value
    # Dont set a register in compare 
    cpu.UpdateFlags(instruction.flags, yVal, value, newVal, True)
    return False

def doDec(cpu, instruction):
    addrVal = GetAddress(cpu, instruction)
    memVal = cpu.ReadMemory(addrVal)

    newVal = memVal - 1
    cpu.SetMemory(addrVal, newVal)
    cpu.UpdateFlags(instruction.flags, memVal, memVal, newVal, True)
    return False

def doDex(cpu, instruction):
    xVal = cpu.GetRegister('X')
    cpu.SetRegister('X', xVal-1)
    cpu.UpdateFlags(instruction.flags, xVal, xVal, xVal-1, True)
    return False

def doDey(cpu, instruction):
    yVal = cpu.GetRegister('Y')
    cpu.SetRegister('Y', yVal-1)
    cpu.UpdateFlags(instruction.flags, yVal, yVal, yVal-1, True)
    return False

def doEor(cpu, instruction):
    aVal = cpu.GetRegister('A')
    value = GetValue(cpu, instruction)

    newVal = aVal ^ value
    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, aVal, value, newVal, False)
    return False

def doInc(cpu, instruction):
    addrVal = GetAddress(cpu, instruction)
    memVal = cpu.ReadMemory(addrVal)

    newVal = memVal + 1
    cpu.SetMemory(addrVal, newVal)
    cpu.UpdateFlags(instruction.flags, memVal, memVal, newVal, False)
    return False 

def doInx(cpu, instruction):
    xVal = cpu.GetRegister('X')
    cpu.SetRegister('X', xVal+1)
    cpu.UpdateFlags(instruction.flags, xVal, xVal, xVal+1, True)
    return False

def doIny(cpu, instruction):
    yVal = cpu.GetRegister('Y')
    cpu.SetRegister('Y', yVal+1)
    cpu.UpdateFlags(instruction.flags, yVal, yVal, yVal+1, True)
    return False

def doJmp(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    cpu.SetPC(addr)
    return True # PC changed by this instruction

def doJsr(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    cpu.PushWord(cpu.GetRegister('PC') + instruction.size)
    cpu.SetPC(addr)
    return True # PC changed by this instruction

def doLda(cpu, instruction):
    value = GetValue(cpu, instruction)
    aVal = cpu.GetRegister('A')
    cpu.SetRegister('A', value)
    cpu.UpdateFlags(instruction.flags, aVal, value, value, False)
    return False

def doLdx(cpu, instruction):
    value = GetValue(cpu, instruction)
    xVal = cpu.GetRegister('X')
    cpu.SetRegister('X', value)
    cpu.UpdateFlags(instruction.flags, xVal, value, value, False)
    return False

def doLdy(cpu, instruction):
    value = GetValue(cpu, instruction)
    yVal = cpu.GetRegister('Y')
    cpu.SetRegister('Y', value)
    cpu.UpdateFlags(instruction.flags, yVal, value, value, False)
    return False

def doLsrAcc(cpu, instruction):
    aVal = cpu.GetRegister('A')
    newVal = aVal >> 1
    cpu.SetRegister('A', newVal)
    cBit = aVal & 1
    cpu.SetFlag('C', cBit)
    cpu.UpdateFlags(instruction.flags, aVal, aVal, newVal, True)
    return False

def doLsr(cpu, instruction):
    address = GetAddress(cpu, instruction)
    value = cpu.ReadMemory(address)
    newVal = value >> 1
    cpu.SetMemory(address, newVal)
    cBit = value & 1
    cpu.SetFlag('C', cBit)
    cpu.UpdateFlags(instruction.flags, value, value, newVal, True)
    return False

def doNop(cpu, instruction):
    return False

def doOra(cpu, instruction):
    value = GetValue(cpu, instruction)
    aVal = cpu.GetRegister('A')

    newVal = aVal | value

    cpu.UpdateFlags(instruction.flags, aVal, value, newVal, False)
    return False

def doPha(cpu, instruction):
    aVal = cpu.GetRegister('A')
    cpu.PushByte(aVal)
    return False

def doPhp(cpu, instruction):
    srVal = cpu.GetRegister('P')
    cpu.PushByte(srVal)
    return False

def doPla(cpu, instruction):
    aVal = cpu.PopByte()
    cpu.SetRegister('A', aVal)
    cpu.UpdateFlags(instruction.flags, aVal, aVal, aVal, False)
    return False

def doPlp(cpu, instruction):
    cpu.setRegister('P', cpu.PopByte())
    return False

def doRolAcc(cpu, instruction):
    value = cpu.GetRegister('A')
    oldC = cpu.GetFlag('C')
    newC = 1 if (value & 0x80) else 0
    newVal = (value << 1 ) + oldC
    cpu.SetRegister('A', newVal)
    cpu.SetFlag('C', newC)
    cpu.UpdateFlags(instruction.flags, value, value, newVal, False)
    return False

def doRol(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    value = cpu.ReadMemory(addr)
    oldC = cpu.GetFlag('C')
    newC = 1 if (value & 0x80) else 0
    newVal = (value << 1 ) + oldC
    cpu.SetMemory(addr, newVal)
    cpu.SetFlag('C', newC)
    cpu.UpdateFlags(instruction.flags, value, value, newVal, False)
    return False

def doRorAcc(cpu, instruction):
    value = cpu.GetRegister('A')
    oldC = cpu.GetFlag('C')
    newC = 1 if (value & 0x1) else 0
    newVal = (value >> 1 ) + (oldC * 0x80)
    cpu.SetRegister('A', newVal)
    cpu.SetFlag('C', newC)
    cpu.UpdateFlags(instruction.flags, value, value, newVal, False)
    return False

def doRor(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    value = cpu.ReadMemory(addr)
    oldC = cpu.GetFlag('C')
    newC = 1 if (value & 0x1) else 0
    newVal = (value >> 1 ) + (oldC * 0x80)
    cpu.SetMemory(addr, newVal)
    cpu.SetFlag('C', newC)
    cpu.UpdateFlags(instruction.flags, value, value, newVal, False)
    return False

def doRti(cpu, instruction):
    cpu.SetRegister('P', cpu.PopByte())
    cpu.SetPC(cpu.PopWord())
    return True

def doRts(cpu, instruction):
    cpu.SetPC(cpu.PopWord())
    return True

def doSbc(cpu, instruction):
    aVal = cpu.GetRegister('A')
    value = GetValue(cpu, instruction)
    cVal = cpu.GetFlag('C')

    newVal = aVal - value - cVal

    cpu.SetRegister('A', newVal)
    cpu.UpdateFlags(instruction.flags, aVal, value, newVal, True)
    return False

def doSec(cpu, instruction):
    cpu.SetFlag('C', 1)
    return False

def doSed(cpu, instruction):
    cpu.SetFlag('D', 1)
    return False

def doSei(cpu, instruction):
    cpu.SetFlag('I', 1)
    return False

def doSta(cpu, instruction):
    aVal = cpu.GetRegister('A')
    addr = GetAddress(cpu, instruction)

    cpu.SetMemory(addr, aVal)
    return False

def doStx(cpu, instruction):
    xVal = cpu.GetRegister('X')
    addr = GetAddress(cpu, instruction)

    cpu.SetMemory(addr, xVal)
    return False

def doSty(cpu, instruction):
    yVal = cpu.GetRegister('Y')
    addr = GetAddress(cpu, instruction)

    cpu.SetMemory(addr, yVal)
    return False

def doTax(cpu, instruction):
    aVal = cpu.GetRegister('A')
    cpu.SetRegister('X', aVal)

    cpu.UpdateFlags(instruction.flags, aVal, aVal, aVal, False)
    return False

def doTay(cpu, instruction):
    aVal = cpu.GetRegister('A')
    cpu.SetRegister('Y', aVal)

    cpu.UpdateFlags(instruction.flags, aVal, aVal, aVal, False)
    return False

def doTsx(cpu, instruction):
    sVal = cpu.GetRegister('S')
    cpu.SetRegister('X', sVal)

    cpu.UpdateFlags(instruction.flags, sVal, sVal, sVal, False)
    return False

def doTxa(cpu, instruction):
    xVal = cpu.GetRegister('X')
    cpu.SetRegister('A', xVal)

    cpu.UpdateFlags(instruction.flags, xVal, xVal, xVal, False)
    return False

def doTxs(cpu, instruction):
    xVal = cpu.GetRegister('X')
    cpu.SetRegister('S', xVal)

    cpu.UpdateFlags(instruction.flags, xVal, xVal, xVal, False)
    return False

def doTya(cpu, instruction):
    yVal = cpu.GetRegister('Y')
    cpu.SetRegister('A', xVal)

    cpu.UpdateFlags(instruction.flags, yVal, yVal, yVal, False)
    return False

# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - better clock info
# http://www.6502.org/tutorials/6502opcodes.html - better descriptions
# http://6502.org/tutorials/65c02opcodes.html#3 - additional instructions
flags = {   'ADC': ['N', 'Z', 'C', 'V'],
            'AND': ['N', 'Z'],
            'ASL': ['N', 'Z'], # set C manually
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
            'CMP': ['N', 'Z', 'C'],
            'CPX': ['N', 'Z', 'C'],
            'CPY': ['N', 'Z', 'C'],
            'DEC': ['N', 'Z'],
            'DEX': ['N', 'Z'],
            'DEY': ['N', 'Z'],
            'EOR': ['N', 'Z'],
            'INC': ['N', 'Z'],
            'INX': ['N', 'Z'],
            'INY': ['N', 'Z'],
            'JMP': [],
            'JSR': [],
            'LDA': ['N', 'Z'],
            'LDX': ['N', 'Z'],
            'LDY': ['N', 'Z'],
            'LSR': ['Z'], # set C manually
            'NOP': [],
            'ORA': ['N', 'Z'],
            'PHA': [],
            'PHP': [],
            'PLA': ['N', 'Z'],
            'PLP': [],
            'ROL': ['N', 'Z'], # manual C
            'ROR': ['N', 'Z'], # manual C
            'RTI': [],
            'RTS': [],
            'SBC': ['N', 'C', 'Z', 'V'],
            'SEC': [],
            'SED': [],
            'SEI': [],
            'STA': [],
            'STX': [],
            'STY': [],
            'TAX': ['N', 'Z'],
            'TAY': ['N', 'Z'],
            'TSX': ['N', 'Z'],
            'TXA': ['N', 'Z'],
            'TXS': ['N', 'Z'],
            'TYA': ['N', 'Z'],
        }

           # opcode : Instruction(mnem, function, operType, size, cycles) 
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
                0xC9: Instruction('CMP', doCmp, 'IMM', 2, 2),
                0xC5: Instruction('CMP', doCmp, 'ZERO', 2, 3),
                0xD5: Instruction('CMP', doCmp, 'ZEROX', 2, 4),
                0xCD: Instruction('CMP', doCmp, 'ABS', 3, 4),
                0xDD: Instruction('CMP', doCmp, 'ABSX', 3, 4),
                0xC1: Instruction('CMP', doCmp, 'INDX', 2, 6),
                0xD1: Instruction('CMP', doCmp, 'INDY', 2, 5),
                0xE0: Instruction('CPX', doCpx, 'IMM', 2, 2),
                0xE4: Instruction('CPX', doCpx, 'ZERO', 2, 3),
                0xEC: Instruction('CPX', doCpx, 'ABS', 3, 4),
                0xC0: Instruction('CPY', doCpy, 'IMM', 2, 2),
                0xC4: Instruction('CPY', doCpy, 'ZERO', 2, 3),
                0xCC: Instruction('CPY', doCpy, 'ABS', 3, 4),
                0xC6: Instruction('DEC', doDec, 'ZERO', 2, 5),
                0xD6: Instruction('DEC', doDec, 'ZEROX', 2, 6),
                0xCE: Instruction('DEC', doDec, 'ABS', 3, 3),
                0xDE: Instruction('DEC', doDec, 'ABSX', 3, 7),
                0xCA: Instruction('DEX', doDex, '', 1, 2),
                0x88: Instruction('DEY', doDey, '', 1, 2),
                0x49: Instruction('EOR', doEor, 'IMM', 2, 2),
                0x45: Instruction('EOR', doEor, 'ZERO', 2, 3),
                0x55: Instruction('EOR', doEor, 'ZEROX', 2, 4),
                0x4D: Instruction('EOR', doEor, 'ABS', 3, 4),
                0x5D: Instruction('EOR', doEor, 'ABSX', 3, 4),
                0x59: Instruction('EOR', doEor, 'ABSY', 3, 4),
                0x41: Instruction('EOR', doEor, 'INDX', 2, 6),
                0x51: Instruction('EOR', doEor, 'INDY', 2, 5),
                0xE6: Instruction('INC', doInc, 'ZERO', 2, 5),
                0xF6: Instruction('INC', doInc, 'ZEROX', 2, 6),
                0xEE: Instruction('INC', doInc, 'ABS', 3, 6),
                0xFE: Instruction('INC', doInc, 'ABSX', 3, 7),
                0xE8: Instruction('INX', doInx, '', 1, 2),
                0xC8: Instruction('INY', doIny, '', 1, 2),
                0x4C: Instruction('JMP', doJmp, 'ABS', 3, 3),
                0x6C: Instruction('JMP', doJmp, 'IND', 3, 3),
                0x20: Instruction('JSR', doJsr, 'ABS', 3, 6),
                0xA9: Instruction('LDA', doLda, 'IMM', 2, 2),
                0xA5: Instruction('LDA', doLda, 'ZERO', 2, 3),
                0xB5: Instruction('LDA', doLda, 'ZEROX', 2, 4),
                0xAD: Instruction('LDA', doLda, 'ABS', 3, 4),
                0xBD: Instruction('LDA', doLda, 'ABSX', 3, 4),
                0xB9: Instruction('LDA', doLda, 'ABSY', 3, 4),
                0xA1: Instruction('LDA', doLda, 'INDX', 2, 6),
                0xB1: Instruction('LDA', doLda, 'INDY', 2, 5),
                0xA2: Instruction('LDX', doLdx, 'IMM', 2, 2),
                0xA6: Instruction('LDX', doLdx, 'ZERO', 2, 3),
                0xB6: Instruction('LDX', doLdx, 'ZEROY', 2, 4),
                0xAE: Instruction('LDX', doLdx, 'ABS', 3, 4),
                0xBE: Instruction('LDX', doLdx, 'ABSY', 3, 4),
                0xA0: Instruction('LDY', doLdy, 'IMM', 2, 2),
                0xA4: Instruction('LDY', doLdy, 'ZERO', 2, 3),
                0xB4: Instruction('LDY', doLdy, 'ZEROX', 2, 4),
                0xAC: Instruction('LDY', doLdy, 'ABS', 3, 4),
                0xBC: Instruction('LDY', doLdy, 'ABSX', 3, 4),
                0x4A: Instruction('LSR', doLsrAcc, '', 1, 2),
                0x46: Instruction('LSR', doLsr, 'ZERO', 2, 5),
                0x56: Instruction('LSR', doLsr, 'ZEROX', 2, 6),
                0x4E: Instruction('LSR', doLsr, 'ABS', 3, 6),
                0x5E: Instruction('LSR', doLsr, 'ABSX', 3, 7),
                0xEA: Instruction('NOP', doNop, '', 1, 2),
                0x09: Instruction('ORA', doOra, 'IMM', 2, 2),
                0x05: Instruction('ORA', doOra, 'ZERO', 2, 3),
                0x15: Instruction('ORA', doOra, 'ZEROX', 2, 4),
                0x0D: Instruction('ORA', doOra, 'ABS', 3, 4),
                0x1D: Instruction('ORA', doOra, 'ABSX', 3, 4),
                0x19: Instruction('ORA', doOra, 'ABSY', 3, 4),
                0x01: Instruction('ORA', doOra, 'INDX', 2, 6),
                0x11: Instruction('ORA', doOra, 'INDY', 2, 5),
                0x48: Instruction('PHA', doPha, '', 1, 3),
                0x08: Instruction('PHP', doPhp, '', 1, 3),
                0x68: Instruction('PLA', doPla, '', 1, 4),
                0x28: Instruction('PLP', doPlp, '', 1, 4),
                0x2A: Instruction('ROL', doRolAcc, '', 1, 2),
                0x26: Instruction('ROL', doRol, 'ZERO', 2, 5),
                0x36: Instruction('ROL', doRol, 'ZEROX', 2, 6),
                0x2E: Instruction('ROL', doRol, 'ABS', 3, 6),
                0x3E: Instruction('ROL', doRol, 'ABSX', 3, 7),
                0x6A: Instruction('ROR', doRorAcc, '', 1, 2),
                0x66: Instruction('ROR', doRor, 'ZERO', 2, 5),
                0x76: Instruction('ROR', doRor, 'ZEROX', 2, 6),
                0x6E: Instruction('ROR', doRor, 'ABS', 3, 6),
                0x7E: Instruction('ROR', doRor, 'ABSX', 3, 7),   
                0x40: Instruction('RTI', doRti, '', 1, 6),
                0x60: Instruction('RTS', doRts, '', 1, 6),
                0xE9: Instruction('SBC', doSbc, 'IMM', 2, 2),
                0xE5: Instruction('SBC', doSbc, 'ZERO', 2, 3),
                0xF5: Instruction('SBC', doSbc, 'ZEROX', 2, 4),
                0xED: Instruction('SBC', doSbc, 'ABS', 3, 4),
                0xFD: Instruction('SBC', doSbc, 'ABSX', 3, 4),
                0xF9: Instruction('SBC', doSbc, 'ABSY', 3, 4),
                0xE1: Instruction('SBC', doSbc, 'INDX', 2, 6),
                0xF1: Instruction('SBC', doSbc, 'INDY', 2, 5),
                0x38: Instruction('SEC', doSec, '', 1, 2),
                0xF8: Instruction('SED', doSed, '', 1, 2),
                0x78: Instruction('SEI', doSei, '', 1, 2),
                0x85: Instruction('STA', doSta, 'ZERO', 2, 3),
                0x95: Instruction('STA', doSta, 'ZEROX', 2, 4),
                0x8D: Instruction('STA', doSta, 'ABS', 3, 4),
                0x9D: Instruction('STA', doSta, 'ABSX', 3, 5),
                0x99: Instruction('STA', doSta, 'ABSY', 3, 5),
                0x81: Instruction('STA', doSta, 'INDX', 2, 6),
                0x91: Instruction('STA', doSta, 'INDY', 2, 6),
                0x86: Instruction('STX', doStx, 'ZERO', 2, 3),
                0x96: Instruction('STX', doStx, 'ZEROY', 2, 4),
                0x8E: Instruction('STX', doStx, 'ABS', 3, 4),
                0x84: Instruction('STY', doSty, 'ZERO', 2, 3),
                0x94: Instruction('STY', doSty, 'ZEROX', 2, 4),
                0x8C: Instruction('STY', doSty, 'ABS', 3, 4),
                0xAA: Instruction('TAX', doTax, '', 1, 2),
                0xA8: Instruction('TAY', doTay, '', 1, 2),
                0xBA: Instruction('TSX', doTsx, '', 1, 2),
                0x8A: Instruction('TXA', doTxa, '', 1, 2),
                0x9A: Instruction('TXS', doTxs, '', 1, 2),
                0x98: Instruction('TYA', doTya, '', 1, 2),
                }
