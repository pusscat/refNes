"""
instructions: the semantic functions for the emulation of 6502 instructions.
"""

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
            cpu.inc_pc(self.size)
        cpu.inc_cycles(self.cycles + self.extraCycles)
        self.extraCycles = 0

    def addCycles(self, cycles):
        self.extraCycles = cycles

# instruction functions return True if they modify PC
# return false otherwise

def GetValue(cpu, instruction):
    operType = instruction.operType
    if operType is 'IMM':
        return cpu.read_rel_pc(1)
    if operType is 'ZERO':
        return cpu.read_memory(cpu.read_rel_pc(1))
    if operType is 'ZEROX':
        # CANNOT CROSS PAGE BOUNDARY SO MASK READ ADDRESS
        return cpu.read_memory((cpu.read_rel_pc(1) + cpu.get_register('X')) & 0xFF)
    if operType is 'ZEROY':
        return cpu.read_memory((cpu.read_rel_pc(1) + cpu.get_register('Y')) & 0xFF)
    if operType is 'ABS':
        return cpu.read_memory((cpu.read_rel_pc(2) << 8) + cpu.read_rel_pc(1))
    if operType is 'ABSX': # THIS CAN CROSS PAGE BOUNDARY
        lowOrder = cpu.read_rel_pc(1) + cpu.get_register('X')
        hiOrder = cpu.read_rel_pc(2)
        if lowOrder > 0xFF:
            instruction.addCycles(1)
        return cpu.read_memory((hiOrder << 8) + lowOrder)
    if operType is 'ABSY':
        lowOrder = cpu.read_rel_pc(1) + cpu.get_register('Y')
        if lowOrder > 0xFF:
            instruction.addCycles(1)
        return cpu.read_memory((cpu.read_rel_pc(2) << 8) + lowOrder)
    if operType is 'INDX':
        addrPtr = cpu.read_mem_word_bug((cpu.read_rel_pc(1) + cpu.get_register('X')) & 0xFF)
        return cpu.read_memory(addrPtr)
    if operType is 'INDY':
        lowOrder = cpu.read_mem_word_bug(cpu.read_rel_pc(1)) + cpu.get_register('Y')
        lowOrder = lowOrder & 0xFFFF
        if lowOrder > 0xFF:
            instruction.addCycles(1)
        return cpu.read_memory(lowOrder)
    if operType is 'PCREL':
        pcReg = cpu.get_register('PC') + instruction.size
        # DO NOT & lo with 0xFF if pos - this can traverse page boundaries
        offset = cpu.read_rel_pc(1)
        if offset < 0x80:
            return pcReg + offset
        else:
            return pcReg + offset - 0x100
    return value

def GetAddress(cpu, instruction):
    operType = instruction.operType
    if operType is 'ZERO':
        return cpu.read_rel_pc(1)
    if operType is 'ZEROX':
        return ((cpu.read_rel_pc(1) + cpu.get_register('X')) & 0xFF)
    if operType is 'ZEROY':
        return ((cpu.read_rel_pc(1) + cpu.get_register('Y')) & 0xFF)
    if operType is 'ABS':
        return (cpu.read_rel_pc(2) << 8) + cpu.read_rel_pc(1)
    if operType is 'ABSX':
        return (cpu.read_rel_pc(2) << 8) + cpu.read_rel_pc(1) + cpu.get_register('X')
    if operType is 'ABSY':
        return ((cpu.read_rel_pc(2) << 8) + cpu.read_rel_pc(1) + cpu.get_register('Y')) & 0xFFFF
    if operType is 'IND':
        addr = cpu.read_mem_word_bug((cpu.read_rel_pc(2) << 8) + cpu.read_rel_pc(1))
        addr = addr & 0xFFFF
        return addr
    if operType is 'INDX':
        return cpu.read_mem_word_bug((cpu.read_rel_pc(1) + cpu.get_register('X')) & 0xFF)
    if operType is 'INDY':
        lowOrder = cpu.read_mem_word_bug(cpu.read_rel_pc(1)) + cpu.get_register('Y')
        lowOrder = lowOrder & 0xFFFF
        if lowOrder > 0xFF:
            instruction.addCycles(1)
            # we should NOT add 1 to high order in this case.
        return lowOrder

    return None


def doAdc(cpu, instruction):
    value = GetValue(cpu, instruction)
    accuVal = cpu.get_register('A')
    carryVal = cpu.get_flag('C')

    newVal = accuVal + value + carryVal

    cpu.set_register('A', newVal)
    cpu.ctrl_update_flags(instruction.flags, accuVal, value, newVal, False)
    return False

def doAnd(cpu, instruction):
    value = GetValue(cpu, instruction)
    accuVal = cpu.get_register('A')

    newVal = accuVal & value

    cpu.set_register('A', newVal)
    cpu.ctrl_update_flags(instruction.flags, accuVal, value, newVal, False)
    return False

def doAsl(cpu, instruction):
    address = GetAddress(cpu, instruction)
    memVal = cpu.read_memory(address)

    newVal = memVal << 1

    if newVal > 0xFF:
        cpu.set_flag('C', 1)
    else:
        cpu.set_flag('C', 0)
    cpu.set_memory(address, newVal)
    cpu.ctrl_update_flags(instruction.flags, memVal, memVal, newVal, False)
    return False

def doAslAccu(cpu, instruction):
    accuVal = cpu.get_register('A')

    newVal = accuVal << 1

    if newVal > 0xFF:
        cpu.set_flag('C', 1)
    else:
        cpu.set_flag('C', 0)

    cpu.set_register('A', newVal)
    cpu.ctrl_update_flags(instruction.flags, accuVal, accuVal, newVal, False)
    return False


def doBranch(cpu, instruction, flag, value):
    if cpu.get_flag(flag) != value:
        return False

    target = GetValue(cpu, instruction)
    currPC = cpu.get_register('PC')
    cpu.set_pc(target)

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
    accuVal = cpu.get_register('A')

    cpu.set_flag('N', (value>>7)&1)
    cpu.set_flag('V', (value>>6)&1)
    cpu.set_flag('Z', 0 if value & accuVal != 0 else 1)
    return False

def doBmi(cpu, instruction):
    return doBranch(cpu, instruction, 'N', 1)

def doBne(cpu, instruction):
    return doBranch(cpu, instruction, 'Z', 0)

def doBpl(cpu, instruction):
    return doBranch(cpu, instruction, 'N', 0)

def doBrk(cpu, instruction):
    cpu.push_word(cpu.get_register('PC')+2)
    cpu.push_byte(cpu.get_register('S'))
    cpu.set_flag('I', 1)
    cpu.set_flag('B', 1)

    # jmp to irqBrk vector
    target = cpu.read_mem_word(cpu.irq_brk_vector)
    cpu.set_pc(target)
    cpu.paused = True
    return True

def doBvc(cpu, instruction):
    return doBranch(cpu, instruction, 'V', 0)

def doBvs(cpu, instruction):
    return doBranch(cpu, instruction, 'V', 1)

def doClc(cpu, instruction):
    cpu.set_flag('C', 0)
    return False

def doCld(cpu, instruction):
    cpu.set_flag('D', 0)
    return False

def doCli(cpu, instruction):
    cpu.set_flag('I', 0)
    return False

def doClv(cpu, instruction):
    cpu.set_flag('V', 0)
    return False

def doCmp(cpu, instruction):
    value = GetValue(cpu, instruction)
    accuVal = cpu.get_register('A')

    newVal = accuVal - value
    # Dont set a register in compare
    if accuVal >= value:
        cpu.set_flag('C', 1)
    else:
        cpu.set_flag('C', 0)
    cpu.ctrl_update_flags(instruction.flags, accuVal, value, newVal, True)
    return False

def doCpx(cpu, instruction):
    value = GetValue(cpu, instruction)
    xVal = cpu.get_register('X')

    newVal = xVal - value
    # Don't set a register in compare
    if xVal >= value:
        cpu.set_flag('C', 1)
    else:
        cpu.set_flag('C', 0)
    cpu.ctrl_update_flags(instruction.flags, xVal, value, newVal, True)
    return False

def doCpy(cpu, instruction):
    value = GetValue(cpu, instruction)
    yVal = cpu.get_register('Y')

    newVal = yVal - value
    # Don't set a register in compare
    if yVal >= value:
        cpu.set_flag('C', 1)
    else:
        cpu.set_flag('C', 0)
    cpu.ctrl_update_flags(instruction.flags, yVal, value, newVal, True)
    return False

def doDec(cpu, instruction):
    addrVal = GetAddress(cpu, instruction)
    memVal = cpu.read_memory(addrVal)

    newVal = memVal - 1
    cpu.set_memory(addrVal, newVal)
    cpu.ctrl_update_flags(instruction.flags, memVal, 1, newVal, True)
    return False

def doDex(cpu, instruction):
    xVal = cpu.get_register('X')
    cpu.set_register('X', xVal-1)
    cpu.ctrl_update_flags(instruction.flags, xVal, 1, xVal-1, True)
    return False

def doDey(cpu, instruction):
    yVal = cpu.get_register('Y')
    cpu.set_register('Y', yVal-1)
    cpu.ctrl_update_flags(instruction.flags, yVal, 1, yVal-1, True)
    return False

def doEor(cpu, instruction):
    aVal = cpu.get_register('A')
    value = GetValue(cpu, instruction)

    newVal = aVal ^ value
    cpu.set_register('A', newVal)
    cpu.ctrl_update_flags(instruction.flags, aVal, value, newVal, False)
    return False

def doInc(cpu, instruction):
    addrVal = GetAddress(cpu, instruction)
    memVal = cpu.read_memory(addrVal)

    newVal = (memVal + 1) & 0xFF
    cpu.set_memory(addrVal, newVal)
    cpu.ctrl_update_flags(instruction.flags, memVal, memVal, newVal, False)
    return False

def doInx(cpu, instruction):
    xVal = cpu.get_register('X')
    cpu.set_register('X', xVal+1)
    cpu.ctrl_update_flags(instruction.flags, xVal, xVal, (xVal+1)&0xFF, False)
    return False

def doIny(cpu, instruction):
    yVal = cpu.get_register('Y')
    cpu.set_register('Y', yVal+1)
    cpu.ctrl_update_flags(instruction.flags, yVal, yVal, (yVal+1)&0xFF, False)
    return False

def doJmp(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    cpu.set_pc(addr)
    return True # PC changed by this instruction

def doJsr(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    cpu.push_word(cpu.get_register('PC') + instruction.size - 1)
    cpu.set_pc(addr)
    return True # PC changed by this instruction

def doLda(cpu, instruction):
    value = GetValue(cpu, instruction)
    aVal = cpu.get_register('A')
    cpu.set_register('A', value)
    cpu.ctrl_update_flags(instruction.flags, aVal, value, value, False)
    return False

def doLdx(cpu, instruction):
    value = GetValue(cpu, instruction)
    xVal = cpu.get_register('X')
    cpu.set_register('X', value)
    cpu.ctrl_update_flags(instruction.flags, xVal, value, value, False)
    return False


def doLax(cpu, instruction):
    value = GetValue(cpu, instruction)
    xVal = cpu.get_register('X')
    cpu.set_register('A', value)
    cpu.set_register('X', value)
    cpu.ctrl_update_flags(instruction.flags, xVal, value, value, False)
    return False

def doSax(cpu, instruction):
    value = GetValue(cpu, instruction)
    xVal = cpu.get_register('X')
    aVal = cpu.get_register('A')

    newVal = (aVal & xVal) - value
    cpu.set_register('X', newVal)
    cpu.ctrl_update_flags(instruction.flags, xVal, aVal, newVal, True)
    return False

def doAxs(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    xVal = cpu.get_register('X')
    aVal = cpu.get_register('A')

    newVal = (aVal & xVal)
    cpu.set_memory(addr, newVal)
    return False

def doLdy(cpu, instruction):
    value = GetValue(cpu, instruction)
    yVal = cpu.get_register('Y')
    cpu.set_register('Y', value)
    cpu.ctrl_update_flags(instruction.flags, yVal, value, value, False)
    return False

def doLsrAcc(cpu, instruction):
    aVal = cpu.get_register('A')
    newVal = aVal >> 1
    cpu.set_register('A', newVal)
    cBit = aVal & 1
    cpu.set_flag('C', cBit)
    cpu.ctrl_update_flags(instruction.flags, aVal, aVal, newVal, True)
    return False

def doLsr(cpu, instruction):
    address = GetAddress(cpu, instruction)
    value = cpu.read_memory(address)
    newVal = value >> 1
    cpu.set_memory(address, newVal)
    cBit = value & 1
    cpu.set_flag('C', cBit)
    cpu.ctrl_update_flags(instruction.flags, value, value, newVal, True)
    return False

def doNop(cpu, instruction):
    return False

def doOra(cpu, instruction):
    value = GetValue(cpu, instruction)
    aVal = cpu.get_register('A')

    newVal = aVal | value
    cpu.set_register('A', newVal)
    cpu.ctrl_update_flags(instruction.flags, aVal, value, newVal, False)
    return False

def doPha(cpu, instruction):
    aVal = cpu.get_register('A')
    cpu.push_byte(aVal)
    return False

def doPhp(cpu, instruction):
    srVal = cpu.get_register('P')
    cpu.push_byte(srVal | 0x10)
    return False

def doPla(cpu, instruction):
    aVal = cpu.pop_byte()
    cpu.set_register('A', aVal)
    cpu.ctrl_update_flags(instruction.flags, aVal, aVal, aVal, False)
    return False

def doPlp(cpu, instruction):
    cpu.set_register('P', cpu.pop_byte() & 0xEF | 0x20)
    return False

def doRolAcc(cpu, instruction):
    value = cpu.get_register('A')
    oldC = cpu.get_flag('C')
    newC = 1 if (value & 0x80) else 0
    newVal = (value << 1) + oldC
    cpu.set_register('A', newVal)
    cpu.set_flag('C', newC)
    cpu.ctrl_update_flags(instruction.flags, value, value, newVal, False)
    return False

def doRol(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    value = cpu.read_memory(addr)
    oldC = cpu.get_flag('C')
    newC = 1 if (value & 0x80) else 0
    newVal = (value << 1) + oldC
    cpu.set_memory(addr, newVal)
    cpu.set_flag('C', newC)
    cpu.ctrl_update_flags(instruction.flags, value, value, newVal, False)
    return False

def doRorAcc(cpu, instruction):
    value = cpu.get_register('A')
    oldC = cpu.get_flag('C')
    newC = 1 if (value & 0x1) else 0
    newVal = (value >> 1) + (oldC * 0x80)
    cpu.set_register('A', newVal)
    cpu.set_flag('C', newC)
    cpu.ctrl_update_flags(instruction.flags, value, value, newVal, False)
    return False

def doRor(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    value = cpu.read_memory(addr)
    oldC = cpu.get_flag('C')
    newC = 1 if (value & 0x1) else 0
    newVal = (value >> 1) + (oldC * 0x80)
    cpu.set_memory(addr, newVal)
    cpu.set_flag('C', newC)
    cpu.ctrl_update_flags(instruction.flags, value, value, newVal, False)
    return False

def doRti(cpu, instruction):
    cpu.set_register('P', cpu.pop_byte())
    cpu.set_pc(cpu.pop_word())
    return True

def doRts(cpu, instruction):
    cpu.set_pc(cpu.pop_word()+1)
    return True

def doSbc(cpu, instruction):
    aVal = cpu.get_register('A')
    value = GetValue(cpu, instruction)
    cVal = cpu.get_flag('C')

    newVal = aVal - value - (1-cVal)

    cpu.set_register('A', newVal)
    cpu.ctrl_update_flags(instruction.flags, aVal, value, newVal, True)
    return False

def doSec(cpu, instruction):
    cpu.set_flag('C', 1)
    return False

def doSed(cpu, instruction):
    cpu.set_flag('D', 1)
    return False

def doSei(cpu, instruction):
    cpu.set_flag('I', 1)
    return False

def doSta(cpu, instruction):
    aVal = cpu.get_register('A')
    addr = GetAddress(cpu, instruction)

    cpu.set_memory(addr, aVal)
    return False

def doStx(cpu, instruction):
    xVal = cpu.get_register('X')
    addr = GetAddress(cpu, instruction)

    cpu.set_memory(addr, xVal)
    return False

def doSty(cpu, instruction):
    yVal = cpu.get_register('Y')
    addr = GetAddress(cpu, instruction)

    cpu.set_memory(addr, yVal)
    return False

def doTax(cpu, instruction):
    aVal = cpu.get_register('A')
    cpu.set_register('X', aVal)

    cpu.ctrl_update_flags(instruction.flags, aVal, aVal, aVal, False)
    return False

def doTay(cpu, instruction):
    aVal = cpu.get_register('A')
    cpu.set_register('Y', aVal)

    cpu.ctrl_update_flags(instruction.flags, aVal, aVal, aVal, False)
    return False

def doTsx(cpu, instruction):
    sVal = cpu.get_register('S')
    cpu.set_register('X', sVal)

    cpu.ctrl_update_flags(instruction.flags, sVal, sVal, sVal, False)
    return False

def doTxa(cpu, instruction):
    xVal = cpu.get_register('X')
    cpu.set_register('A', xVal)

    cpu.ctrl_update_flags(instruction.flags, xVal, xVal, xVal, False)
    return False

def doTxs(cpu, instruction):
    xVal = cpu.get_register('X')
    cpu.set_register('S', xVal)

    cpu.ctrl_update_flags(instruction.flags, xVal, xVal, xVal, False)
    return False

def doTya(cpu, instruction):
    yVal = cpu.get_register('Y')
    cpu.set_register('A', yVal)

    cpu.ctrl_update_flags(instruction.flags, yVal, yVal, yVal, False)
    return False

def doDcm(cpu, instruction):
    addr = GetAddress(cpu, instruction)
    value = (GetValue(cpu, instruction) - 1)
    aVal = cpu.get_register('A')
   
    newVal = aVal - value
    if aVal >= value:
        cpu.set_flag('C', 1)
    else:
        cpu.set_flag('C', 0)
    
    cpu.set_memory(addr, value)
    cpu.ctrl_update_flags(instruction.flags, aVal, value, newVal, True)
    return False

# http://www.e-tradition.net/bytes/6502/6502_instruction_set.html - better clock info
# http://www.6502.org/tutorials/6502opcodes.html - better descriptions
# http://6502.org/tutorials/65c02opcodes.html#3 - additional instructions
flags = {   'ADC': ['N', 'Z', 'C', 'V'],
            'AND': ['N', 'Z'],
            'ASL': ['N', 'Z'], # set C manually
            'AXS': [],
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
            'CMP': ['N', 'Z'],
            'CPX': ['N', 'Z'],
            'CPY': ['N', 'Z'],
            'DCM': ['N', 'Z'],
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
            'LAX': ['N', 'Z'],
            'LSR': ['N', 'Z'], # set C manually
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
            'SAX': ['N', 'C', 'Z'],
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
            'TXS': [],
            'TYA': ['N', 'Z'],
        }

           # opcode : Instruction(mnem, function, operType, size, cycles)
instructions = {0x69: Instruction('ADC', doAdc, 'IMM', 2, 2),
                0x65: Instruction('ADC', doAdc, 'ZERO', 2, 3),
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
                0x24: Instruction('BIT', doBit, 'ZERO', 2, 3),
                0x2C: Instruction('BIT', doBit, 'ABS', 3, 4),
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
                0xD9: Instruction('CMP', doCmp, 'ABSY', 3, 4),
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
                0x6C: Instruction('JMP', doJmp, 'IND', 3, 5),
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
                0x44: Instruction('NOP', doNop, '', 2, 2),
                0x04: Instruction('NOP', doNop, '', 2, 2),
                0x14: Instruction('NOP', doNop, '', 2, 2),
                0x34: Instruction('NOP', doNop, '', 2, 2),
                0x54: Instruction('NOP', doNop, '', 2, 2),
                0x74: Instruction('NOP', doNop, '', 2, 2),
                0xd4: Instruction('NOP', doNop, '', 2, 2),
                0xf4: Instruction('NOP', doNop, '', 2, 2),
                0x64: Instruction('NOP', doNop, '', 2, 2),
                0xDA: Instruction('NOP', doNop, '', 1, 2),
                0x1A: Instruction('NOP', doNop, '', 1, 2),
                0x3A: Instruction('NOP', doNop, '', 1, 2),
                0x5A: Instruction('NOP', doNop, '', 1, 2),
                0x7A: Instruction('NOP', doNop, '', 1, 2),
                0x0C: Instruction('NOP', doNop, '', 3, 2),
                0x1C: Instruction('NOP', doNop, '', 3, 2),
                0x3C: Instruction('NOP', doNop, '', 3, 2),
                0x5C: Instruction('NOP', doNop, '', 3, 2),
                0x7C: Instruction('NOP', doNop, '', 3, 2),
                0xDC: Instruction('NOP', doNop, '', 3, 2),
                0xFC: Instruction('NOP', doNop, '', 3, 2),
                0xFA: Instruction('NOP', doNop, '', 1, 2),
                0x80: Instruction('NOP', doNop, '', 2, 2),
                0x89: Instruction('NOP', doNop, '', 2, 2),
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
                0xEB: Instruction('SBC', doSbc, 'IMM', 2, 2),
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
                0x91: Instruction('STA', doSta, 'INDY', 2, 5),
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
                0xAF: Instruction('LAX', doLax, 'ABS', 3, 4),
                0xBF: Instruction('LAX', doLax, 'ABSY', 3, 5),
                0xA7: Instruction('LAX', doLax, 'ZERO', 2, 3),
                0xB7: Instruction('LAX', doLax, 'ZEROY', 2, 4),
                0xA3: Instruction('LAX', doLax, 'INDX', 2, 6),
                0xB3: Instruction('LAX', doLax, 'INDY', 2, 5),
                0xCB: Instruction('SAX', doSax, 'IMM', 2, 2),
                0x8F: Instruction('AXS', doAxs, 'ABS', 3, 4),
                0x87: Instruction('AXS', doAxs, 'ZERO', 2, 3),
                0x97: Instruction('AXS', doAxs, 'ZEROY', 2, 4),
                0x83: Instruction('AXS', doAxs, 'INDX', 2, 6),
                0xCF: Instruction('DCM', doDcm, 'ABS', 3, 6),
                0xDF: Instruction('DCM', doDcm, 'ABSX', 3, 7),
                0xDB: Instruction('DCM', doDcm, 'ABSY', 3, 7),
                0xC7: Instruction('DCM', doDcm, 'ZERO', 2, 5),
                0xD7: Instruction('DCM', doDcm, 'ZEROX', 2, 6),
                0xC3: Instruction('DCM', doDcm, 'INDX', 2, 8),
                0xD3: Instruction('DCM', doDcm, 'INDY', 2, 8),
               }
